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
- `POST /api/alert`: Receives alert data (`type`, `lat`, `lon`).
- `GET /api/alerts`: Returns the list of all active alerts.
