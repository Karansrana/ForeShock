# SignalFlare: Intelligent Offline Disaster Triage

**Goal:** Solve the "overlooked" problem in large-scale disasters by bridging offline hardware (Arduino) and AI-powered software to create a real-time triage map for first responders.

## Architecture
`Physical Button (Arduino)` $\rightarrow$ `USB Serial` $\rightarrow$ `Python Bridge (bridge.py)` $\rightarrow$ `FastAPI Backend (main.py)` $\rightarrow$ `Real-time Map (Leaflet.js)`

## Tech Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic.
- **Bridge:** Python (`pyserial`, `requests`).
- **Frontend:** HTML, Tailwind CSS, Leaflet.js.
- **Future:** Supabase (Database), Gemini/OpenAI (AI Triage), Vercel (Deployment).

## MVP Definition (Draft 1)
- A physical button press on an Arduino sends a JSON payload.
- The Python bridge forwards this to the FastAPI backend.
- The Leaflet map fetches the alerts every 2 seconds and plots a pin.

## API Endpoints
- `GET /`: Serves the frontend map directly (single origin, no CORS issues).
- `GET /health`: API status check.
- `POST /api/alert`: Receives alert data (`type`, `lat`, `lon`, `urgency`).
- `GET /api/alerts`: Returns the list of all active alerts.

## Progress (updated Nov 7, 2026)
- [x] Backend scaffold (FastAPI, CORS, in-memory store) — running on http://localhost:8000
- [x] Frontend map (Leaflet, dark CSS filter, 3-provider tile fallback) — served at GET /
- [x] Hardware bridge (`bridge.py`) — serial auto-detect, JSON-or-keyword parsing, `--simulate` mode
- [x] Phase 1 core loop verified end-to-end via simulation (SIM alert -> API -> map pin)
- [ ] Real-hardware bench test — blocked on hardware teammate's Arduino
- [x] Phase 2: AI text triage (`POST /api/text-alert` + Gemini + Nominatim geocoding) and SMS simulator UI
- [ ] Phase 3: Supabase persistence, red-zone clustering, stats sidebar

## Rules
- Commit & push to GitHub after every feature/fix (remote: github.com/Karansrana/SignalFlare).
- Never commit secrets: API keys live in `.env` (gitignored). Python runs via the `py` launcher, not `python`.
