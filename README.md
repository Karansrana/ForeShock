# ForeShock — Intelligent Offline Disaster Triage

**ForeShock** bridges offline hardware and AI to solve the "overlooked victim" problem in large-scale disasters: a single physical button press (or a panicked SMS) becomes a structured, prioritized pin on a live triage map that first responders can actually use.

Built as a hackathon project. Pipeline:

```
Physical Button (Arduino) ──USB serial──▶ bridge.py ──HTTP──▶ FastAPI (main.py) ──▶ Live Leaflet map
Raw SMS text ─────────────────────────────▶ POST /api/text-alert ──▶ Groq LLM triage + Nominatim geocoding ──▶ same map
```

## Features

- **Hardware beacon** — Arduino button press → serial → bridge → API → map pin (JSON or bare-keyword payloads both accepted, auto-detects the COM port)
- **AI text triage** — send a messy SOS message; Groq (OpenAI-compatible, free tier) extracts type / urgency / location / summary, and the address is geocoded via OSM Nominatim
- **Live map UI** — dark-themed Leaflet map, polls `/api/alerts` every 2s, urgency-colored markers, SMS simulator panel built in
- **No-hardware demo mode** — `bridge.py --simulate` fakes button presses so the whole loop runs on any laptop

## Quickstart (no hardware needed)

Requires Python 3.10+ and the Windows `py` launcher (or any `python`).

```bash
# 1. Install dependencies
py -m pip install -r requirements.txt

# 2. (Optional) AI triage — copy .env.example to .env and add a free Groq key
#    Get one at https://console.groq.com (no credit card needed)
copy .env.example .env   # then edit .env and set GROQ_API_KEY

# 3. Start the backend (serves the map at http://localhost:8000)
py main.py

# 4. In a second terminal, simulate Arduino button presses
py bridge.py --simulate
```

Open **http://localhost:8000** — pins appear every 5 seconds. Try the **SMS** panel in the header to send a text alert like `"trapped in the library basement, 3rd floor, send help"`.

## Real hardware

```bash
py bridge.py              # auto-detects the Arduino port
py bridge.py --port COM5  # or force a port
```

The Arduino sketch should print one alert per line at 9600 baud, either as JSON
(`{"type": "MEDICAL", "lat": 32.98, "lon": -96.75}`) or a bare keyword (`MEDICAL`).

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/` | Serves the map frontend (single origin, no CORS issues) |
| GET  | `/health` | Status check |
| POST | `/api/alert` | Receive a beacon alert (`type`, `lat`, `lon`, `urgency`) |
| POST | `/api/text-alert` | AI triage of a raw text message (`text`, optional `demo_coords`) |
| GET  | `/api/alerts` | All active alerts |

Alert types: `MEDICAL`, `TRAPPED`, `SUPPLIES`, `SAFE`. Urgency is 0–10.

## Tech stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic
- **Bridge:** Python (`pyserial`, `requests`)
- **AI triage:** Groq API (OpenAI-compatible) + OSM Nominatim geocoding
- **Frontend:** HTML, Tailwind CSS, Leaflet.js (dark tiles via CSS filter, 3-provider tile fallback)

## Notes & limitations

- Alerts are stored in memory — they reset when the server restarts (MVP trade-off; Supabase persistence was the planned Phase 3).
- Never commit `.env` — API keys stay local (it's gitignored).

## License

MIT
