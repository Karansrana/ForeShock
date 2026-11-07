from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI(title="SignalFlare Backend")

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

# Temporary In-Memory Database for the MVP
active_alerts = []

BASE_DIR = Path(__file__).resolve().parent

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serves the map directly from the API — one origin, no CORS or file:// issues."""
    return FileResponse(BASE_DIR / "index.html")

@app.get("/health")
async def health():
    return {"message": "SignalFlare API is running. Use /api/alerts to see data."}

@app.post("/api/alert")
async def receive_alert(alert: Alert):
    """
    Endpoint for the bridge.py script to post data from the Arduino.
    """
    alert_dict = alert.dict()
    active_alerts.append(alert_dict)
    print(f"🚨 Received {alert.type} alert at {alert.lat}, {alert.lon} (Urgency: {alert.urgency})")
    return {"status": "success", "message": "Alert logged successfully"}

@app.get("/api/alerts", response_model=List[dict])
async def get_all_alerts():
    """
    Endpoint for the Leaflet.js frontend to fetch all active pins.
    """
    return active_alerts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
