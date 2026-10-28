# Configuration

All configuration is through environment variables.

## Backend

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379` | Redis for pub/sub fan-out and telemetry cache. Unreachable → runs without it. |
| `TIMESCALE_URL` | `postgresql://nexus:nexusforge_dev@localhost:5432/nexusforge` | TimescaleDB for telemetry persistence. Unreachable → telemetry is not persisted. |
| `CORS_ORIGINS` | `*` | Comma-separated list of allowed browser origins. Set this explicitly in any shared deployment. |
| `MAX_SESSIONS` | `16` | Maximum concurrent sessions. Each runs its own 60 FPS loop; `POST /sessions` returns 429 at the limit. |
| `ANTHROPIC_API_KEY` | unset | Enables Claude for natural-language command parsing. Without it the keyword parser is used. |

## Dashboard (build time)

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Base URL of the API; the WebSocket URL is derived from it. |

## Limits enforced by the API

- 2–4 teams and 1–32 drones per team at session creation; 128 drones per session in total.
- `quantization_bits` / `bits` must be 4, 8, 16 or 32; `aggression` is 0–1.
- Benchmarks accept 1–10,000 runs and only known models and MCUs
  (`GET /benchmark/models` lists them).
