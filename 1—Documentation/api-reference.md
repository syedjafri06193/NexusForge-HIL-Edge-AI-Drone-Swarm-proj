# API reference

The backend is a FastAPI app (`backend/api/main.py`). When it is running,
interactive OpenAPI docs are served at `/docs`. Request bodies are JSON;
invalid bodies return **422**, unknown teams/missions/models return **400**,
unknown sessions or drones return **404**.

## Sessions

| Method | Path | Body / query | Notes |
|---|---|---|---|
| `GET` | `/health` | | `{status, sessions, redis}` |
| `POST` | `/sessions` | `{num_teams: 2–4, drones_per_team: 1–32}` | 201 with `session_id`; 429 when `MAX_SESSIONS` is reached |
| `GET` | `/sessions` | | Summary of every running session |
| `GET` | `/sessions/{sid}` | | Full snapshot plus leaderboard, swarm and HIL status |
| `DELETE` | `/sessions/{sid}` | | Stops the loop and removes the session |
| `POST` | `/sessions/{sid}/pause` | | Toggles pause; returns `{paused}` |

## Swarm control

| Method | Path | Body | Notes |
|---|---|---|---|
| `POST` | `/sessions/{sid}/command` | `{team, mission, formation?, target_x?, target_y?, source?}` | `team`: RED, BLUE, GREEN, GOLD. `mission`: attack, defend, capture, flank, regroup, scatter, surround, patrol, escort, kamikaze. `formation`: wedge, line, circle, spread, diamond, column |
| `POST` | `/sessions/{sid}/nlp` | `{text, team?}` | Natural-language order, e.g. *"attack the center in wedge formation"* |
| `POST` | `/sessions/{sid}/auto_tactics?enabled=true` | | Toggle the automatic tactical planner |

## Drones

| Method | Path | Body | Notes |
|---|---|---|---|
| `POST` | `/sessions/{sid}/drones` | `{team, model_type?, aggression? 0–1, quantization_bits? 4/8/16/32}` | Max 128 per session |
| `GET` | `/sessions/{sid}/drones/{drone_id}` | | Drone state and latest telemetry |
| `GET` | `/sessions/{sid}/leaderboard` | | |

## Telemetry and hardware-in-the-loop

| Method | Path | Body / query | Notes |
|---|---|---|---|
| `GET` | `/sessions/{sid}/telemetry?n=50` | `n` ≤ 500 | Recent HIL telemetry and fleet health |
| `GET` | `/sessions/{sid}/hil/commands` | | Commands sent to hardware nodes |
| `POST` | `/sessions/{sid}/hil/inject` | `{drone_id, health?, battery_pct? 0–100, pos?: {x, y}}` | Overrides a simulated drone with real hardware readings |

## Edge-AI benchmarks

| Method | Path | Body / query | Notes |
|---|---|---|---|
| `GET` | `/benchmark/models` | | Known models and MCUs |
| `POST` | `/benchmark` | `{model_name?, mcu_type?, bits? 4/8/16/32, n_runs? 1–10000}` | Latency percentiles, energy (µJ), accuracy, budget-met % |
| `POST` | `/benchmark/compare?model_name=&mcu_type=` | | The same model at every bit width |

Models: `obstacle_detector`, `threat_classifier`, `trajectory_predictor`,
`swarm_coordinator`. MCUs: `esp32`, `esp32_s3`, `stm32f4`, `stm32h7`,
`rpi_zero_2`.

## Faults

| Method | Path | Body | Notes |
|---|---|---|---|
| `GET` | `/faults/types` | | All fault types |
| `POST` | `/sessions/{sid}/faults` | `{fault_type, drone_ids?, severity? 0–1, duration_s? 1–120, description?}` | |
| `POST` | `/sessions/{sid}/faults/scenario` | `{scenario}` | `network_degradation`, `battery_crisis`, `inference_failure`, `cascade`, `rogue_unit` |
| `GET` | `/sessions/{sid}/faults` | | Active faults |
| `DELETE` | `/sessions/{sid}/faults` | | Clear all faults |

Fault types: packet_loss_spike, latency_spike, bandwidth_throttle,
mqtt_disconnect, battery_drain, brownout, power_off, cpu_overload,
memory_pressure, inference_corrupt, watchdog_reset, gps_drift, imu_bias,
sensor_freeze, split_brain, command_flood, rogue_drone.

## Replay and analytics

| Method | Path | Query |
|---|---|---|
| `GET` | `/sessions/{sid}/replay` | `start`, `end` (tick indices) |
| `GET` | `/sessions/{sid}/analytics` | |
| `GET` | `/sessions/{sid}/analytics/timeseries/{drone_id}` | |
| `GET` | `/sessions/{sid}/analytics/power` | |
| `GET` | `/sessions/{sid}/analytics/db` | |
| `GET` | `/sessions/{sid}/analytics/cached` | |

## WebSocket: `/sessions/{sid}/ws`

Closes with code 4004 if the session does not exist.

**Server → client**

| Message | When |
|---|---|
| `{"type": "init", tick, elapsed, scores, drones, projectiles, arena, events, swarm_status}` | Once, on connect |
| State snapshot (same fields as `init`, plus `hil_telemetry`, `hil_fleet`, `swarm_status`; no `type`) | Every tick (60 FPS) |
| `{"type": "ping"}` | After 30 s without a client message |
| `{"type": "pong"}` | Reply to a client ping |
| `{"type": "error", "error": "..."}` | Malformed message or unknown team; the connection stays open |

**Client → server**

| Message | Effect |
|---|---|
| `{"type": "command", "team": "RED", "text": "flank the blue team"}` | Natural-language order |
| `{"type": "ping"}` | Server replies `pong` |
