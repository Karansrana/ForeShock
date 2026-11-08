import json
import os
import random
from datetime import datetime, timezone

import openai
import requests
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
from fastapi.responses import FileResponse

# Loads GROQ_API_KEY from .env (that file is gitignored — never commit secrets)
load_dotenv()

app = FastAPI(title="ForeShock Backend")

# CORS Middleware: Allows the frontend HTML file to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Model for an Emergency Alert
class Alert(BaseModel):
    type: str    # e.g., "MEDICAL", "TRAPPED", "SUPPLIES", "SAFE"
    lat: float   # Latitude
    lon: float   # Longitude
    urgency: int = 5  # Default urgency (1-10)
    source: str = "BEACON"   # "BEACON" (Arduino) or "TEXT" (AI-parsed SMS)
    summary: str = ""        # One-line gist of the emergency (AI-generated)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Temporary In-Memory Database for the MVP
active_alerts = []

BASE_DIR = Path(__file__).resolve().parent

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serves the map directly from the API — one origin, no CORS or file:// issues."""
    return FileResponse(BASE_DIR / "index.html")

@app.get("/health")
async def health():
    return {"message": "ForeShock API is running. Use /api/alerts to see data."}

@app.post("/api/alert")
async def receive_alert(alert: Alert):
    """
    Endpoint for the bridge.py script to post data from the Arduino.
    """
    alert.created_at = datetime.now(timezone.utc)
    alert_dict = alert.dict()
    active_alerts.append(alert_dict)
    print(f"🚨 Received {alert.type} alert at {alert.lat}, {alert.lon} (Urgency: {alert.urgency})")
    return {"status": "success", "message": "Alert logged successfully"}

# ================= AI Triage (Phase 2) =================
# Groq — OpenAI-compatible API with a free tier (no credit card needed).
# Get a key at console.groq.com and put it in .env as GROQ_API_KEY=gsk_...
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Groq rotates models often — try these in order, first one that exists wins
GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct-0905",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

TRIAGE_PROMPT = """You are the triage parser for ForeShock, a disaster response system.
Extract structured data from a panicked, messy emergency message.

Return JSON with exactly these fields:
- "type": one of "MEDICAL", "TRAPPED", "SUPPLIES", "SAFE"
- "urgency": integer 1-10 (10 = life-threatening injury, 8 = trapped or urgent danger, 4 = needs supplies but stable, 0 = safe, no help needed)
- "location": the street address or place name mentioned in the message, or "" if none
- "summary": one short sentence a rescue coordinator can read at a glance

Message: "{text}"""


def geocode(location: str):
    """Convert an address/place name into lat/lon using OSM's free Nominatim service."""
    if not location:
        return None
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location, "format": "json", "limit": 1},
            headers={"User-Agent": "ForeShock-Hackathon/1.0"},
            timeout=5,
        )
        results = r.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def fallback_coords():
    """Campus center with slight jitter so overlapping pins stay visible."""
    return (
        32.985 + random.uniform(-0.01, 0.01),
        -96.750 + random.uniform(-0.01, 0.01),
    )


class DemoCoordinates(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class TextAlertRequest(BaseModel):
    text: str
    demo_coords: Optional[DemoCoordinates] = None


@app.post("/api/text-alert", response_model=Alert)
def receive_text_alert(req: TextAlertRequest):
    """
    Receives a raw, messy SOS message (simulating an SMS), uses Groq (Llama) to
    structure it, geocodes the location, and logs it through the exact same
    pipeline as the hardware beacon pings.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="AI not configured. Add GROQ_API_KEY to .env and restart the server.")

    # 1. Ask the LLM to structure the chaos (JSON mode guarantees parseable output)
    client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    parsed = None
    last_err = None
    for model in GROQ_MODELS:
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a strict JSON triage parser. Reply with JSON only."},
                    {"role": "user", "content": TRIAGE_PROMPT.replace("{text}", req.text)},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=15,
            )
            parsed = json.loads(r.choices[0].message.content)
            print(f"🤖 Triage model in use: {model}")
            break
        except openai.NotFoundError as e:
            last_err = e
            continue  # model not available on this account — try the next one
        except openai.AuthenticationError:
            raise HTTPException(status_code=502, detail="Groq rejected the key. Check your GROQ_API_KEY in .env.")
        except (openai.OpenAIError, KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            last_err = e
            continue
    if parsed is None:
        if isinstance(last_err, openai.NotFoundError):
            raise HTTPException(status_code=502, detail="No Groq model available. List yours at console.groq.com or add one to GROQ_MODELS in main.py.")
        raise HTTPException(status_code=502, detail=f"AI triage failed: {type(last_err).__name__}: {str(last_err)[:200]}")

    # 2. Sanitize what the AI returned (never trust it blindly)
    alert_type = str(parsed.get("type", "SUPPLIES")).upper()
    if alert_type not in ("MEDICAL", "TRAPPED", "SUPPLIES", "SAFE"):
        alert_type = "SUPPLIES"
    try:
        urgency = max(0, min(10, int(parsed.get("urgency", 5))))
    except (TypeError, ValueError):
        urgency = 5

    # 3. Use the map-selected demo position when supplied; otherwise geocode the address.
    if req.demo_coords:
        coords = (req.demo_coords.lat, req.demo_coords.lon)
    else:
        coords = geocode(parsed.get("location", "")) or fallback_coords()

    # 4. Same pipeline as the Arduino: append to the shared alert store
    alert = Alert(
        type=alert_type,
        lat=coords[0],
        lon=coords[1],
        urgency=urgency,
        source="TEXT",
        summary=str(parsed.get("summary", ""))[:200],
        created_at=datetime.now(timezone.utc),
    )
    active_alerts.append(alert.dict())
    print(f"💬 Text alert: {alert.type} (urgency {alert.urgency}) at {alert.lat:.4f}, {alert.lon:.4f} — {alert.summary}")
    return alert

@app.get("/api/alerts", response_model=List[dict])
async def get_all_alerts():
    """
    Endpoint for the Leaflet.js frontend to fetch all active pins.
    """
    return active_alerts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
