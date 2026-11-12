# ForeShock — Hackathon Demo

ForeShock is a disaster-response prototype built during a hackathon. It turns
Arduino button alerts or example SMS reports into urgency-coded markers on a
live map. This repository is a demo project, not an official State Farm
product, and is not intended for real emergency response or insurance claims.

## What the demo includes

- **Live triage map** — Leaflet map centered on UT Dallas with alert markers,
  urgency shading, a compact legend, and marker details.
- **SMS simulator** — Groq classifies a sample emergency message and the map
  displays its summary and timestamp.
- **Arduino bridge** — `bridge.py` can read button events over USB serial or
  simulate them locally. Hardware is optional and is not required for the
  hosted demo.

## Deploy the public demo to Render

The included `render.yaml` configures a single Python web service that serves
both the frontend and API from the same origin.

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint**, select this repository, and apply the
   `render.yaml` configuration.
3. In the new service's environment settings, set `GROQ_API_KEY` to a key from
   [Groq Console](https://console.groq.com/). Do not put the key in the
   frontend, source control, or a public document.
4. Wait for the deployment to finish, open the service URL, and check
   `/health`. Try the **Simulate SOS** menu to verify AI triage.

Render deploys the FastAPI backend and `index.html` together. The frontend uses
same-origin API paths, so no separate frontend host or CORS configuration is
needed. The Arduino bridge is intentionally not part of this public demo.

## Run locally

Requires Python 3.10+.

```powershell
py -m pip install -r requirements.txt
Copy-Item .env.example .env
# Add GROQ_API_KEY to .env to enable AI text triage.
py main.py
```

Open <http://localhost:8000>. To generate sample beacon alerts, start a second
terminal and run:

```powershell
py bridge.py --simulate
```

For optional local hardware use, close any serial monitor and run `py
bridge.py`; the bridge auto-detects common Arduino USB serial devices. A direct
API URL can be configured in `bridge.py` if sending to a remote service, but
the hosted demo does not need a bridge.

## Configuration and limits

- `GROQ_API_KEY` enables the SMS triage endpoint. Without it, the map and beacon
  endpoint still work, but text triage returns a configuration error.
- Alerts are held in process memory, capped at the latest 500, and disappear
  when the service restarts or sleeps. This is acceptable only for a showcase.
- Public API rate limits are per application instance: 60 alert-list requests,
  3 shared alert clears, 20 beacon submissions, and 5 AI text submissions per
  IP per minute. Clearing alerts deletes them from the shared demo for everyone.
- The hosted service uses one instance so its in-memory demo state and rate
  limits are shared within that instance. Free hosting may sleep when idle.
- The app uses third-party services for map tiles, Groq AI triage, and
  OpenStreetMap Nominatim geocoding. Their availability and usage limits apply.
- Do not submit real names, phone numbers, policy information, addresses, or
  other sensitive personal data to this public demo.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Frontend map |
| `GET` | `/health` | Health check |
| `GET` | `/api/alerts` | Current in-memory alerts |
| `DELETE` | `/api/alerts` | Clear all shared demo alerts |
| `POST` | `/api/alert` | Beacon alert |
| `POST` | `/api/text-alert` | AI triage of `{ "text": "..." }` |

Alert types are `MEDICAL`, `TRAPPED`, `SUPPLIES`, and `SAFE`; urgency ranges
from 0 to 10.

## License

MIT. See [LICENSE](./LICENSE).
