# ForeShock: Intelligent Offline Disaster Triage

**Goal:** Solve the "overlooked" problem in large-scale disasters by bridging offline hardware (Arduino) and AI-powered software to create a real-time triage map for first responders.

## Architecture
`Physical Button (Arduino)` $\rightarrow$ `USB Serial` $\rightarrow$ `Python Bridge (bridge.py)` $\rightarrow$ `FastAPI Backend (main.py)` $\rightarrow$ `Real-time Map (Leaflet.js)`

## Tech Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic.
- **Bridge:** Python (`pyserial`, `requests`).
- **Frontend:** HTML, Tailwind CSS, Leaflet.js.
- **Deployment:** Public hackathon demo runs as a single Render service using `render.yaml`; Supabase persistence remains future work.

## MVP Definition (Draft 1)
- A physical button press on an Arduino sends a JSON payload.
- The Python bridge forwards this to the FastAPI backend.
- The Leaflet map fetches the alerts every 2 seconds and plots a pin.

## API Endpoints
- `GET /`: Serves the frontend map directly (single origin, no CORS issues).
- `GET /health`: API status check.
- `POST /api/alert`: Receives alert data (`type`, `lat`, `lon`, `urgency`).
- `GET /api/alerts`: Returns the list of all active alerts.

## Progress (updated Nov 12, 2026)
- [x] Backend scaffold (FastAPI, in-memory store, same-origin frontend/API) — running locally on http://localhost:8000
- [x] Frontend map (Leaflet, responsive demo UI, severity markers, impact shading, 3-provider tile fallback)
- [x] Hardware bridge (`bridge.py`) — serial auto-detect, JSON-or-keyword parsing, `--simulate` mode
- [x] Phase 1 core loop verified end-to-end via simulation and Arduino (button -> bridge -> API -> map pin)
- [x] Phase 2: AI text triage (`POST /api/text-alert` + Groq + Nominatim geocoding) and SMS simulator UI
- [ ] Public demo deployment — Render Blueprint is configured; set `GROQ_API_KEY` in Render and deploy.
- [ ] Phase 3: Supabase persistence, red-zone clustering, stats sidebar

## Rules
- Commit & push to GitHub after every feature/fix (remote: github.com/Karansrana/SignalFlare).
- Never commit secrets: API keys live in `.env` (gitignored). Python runs via the `py` launcher, not `python`.
