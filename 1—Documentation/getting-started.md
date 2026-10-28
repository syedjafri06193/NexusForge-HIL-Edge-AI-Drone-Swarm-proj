# Getting started

## Requirements

- Python 3.11 or 3.12 (the pinned `numpy==1.26.4` has no wheels for 3.13)
- Node 20+ for the dashboard
- Docker and Docker Compose for the full stack (optional)
- PlatformIO for the ESP32 firmware (optional)

## Headless (no services)

```bash
pip install -r backend/requirements.txt pytest
pytest                                                     # all tests
python demos/run_demo.py --teams 4 --drones 16 --ticks 600 --faults
```

## Local development

```bash
# terminal 1 — API on http://localhost:8000 (interactive docs at /docs)
uvicorn backend.api.main:app --reload --port 8000

# terminal 2 — dashboard on http://localhost:3000
cd dashboard
npm ci
npm run dev
```

Create a session from the dashboard lobby, or with the API:

```bash
curl -X POST localhost:8000/sessions -H 'Content-Type: application/json' \
  -d '{"num_teams": 2, "drones_per_team": 8}'
```

## Full stack with Docker Compose

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API + OpenAPI docs | http://localhost:8000/docs |
| MQTT broker | `localhost:1883` (WebSocket on 9001) |
| Redis | `localhost:6379` |

## Kubernetes

`infra/k8s/nexusforge-k8s.yaml` defines a namespace, a ConfigMap, Redis,
API and dashboard Deployments with Services, an Ingress, and a
HorizontalPodAutoscaler for the API. Build and push the images from
`infra/docker/` and update the `nexusforge/api:latest` and
`nexusforge/dashboard:latest` references first.

## Building the ESP32 firmware

```bash
cd firmware/esp32_sim
pio run -t upload
```

Edit the `#define`s at the top of `main.cpp` — `WIFI_SSID`, `WIFI_PASS`,
`MQTT_BROKER` (the server's IP), `SESSION_ID` and `DRONE_ID` — before
flashing. See
[hardware-in-the-loop.md](hardware-in-the-loop.md).
