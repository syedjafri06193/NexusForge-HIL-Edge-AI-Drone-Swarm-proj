# Architecture

NexusForge is a real-time, multi-agent drone combat simulator that couples a
Python simulation with edge-AI and hardware-in-the-loop (HIL) models, a
FastAPI backend and a React dashboard.

```
ESP32 / STM32 boards ──MQTT──► Mosquitto ─┐
                                          ▼
                      ┌──────────── FastAPI backend (backend/api/main.py) ────────────┐
                      │  GameSession (one per session id)                              │
                      │   ├─ Simulation        simulation/engine/sim.py   60 FPS loop  │
                      │   ├─ SwarmOrchestrator agents/swarm/orchestrator.py            │
                      │   ├─ HILManager        firmware/protocols/hil_mqtt.py          │
                      │   ├─ FaultInjector     firmware/fault_injection/injector.py    │
                      │   ├─ DroneInferencePool firmware/tinyml/inference.py           │
                      │   └─ TelemetryWriter   backend/telemetry/writer.py             │
                      └───────┬───────────────────────────┬───────────────────────────┘
                              │ WebSocket (state @ 60 FPS) │ Redis pub/sub · TimescaleDB
                              ▼                            ▼
                     React dashboard (dashboard/)     other API replicas, analytics
```

## The tick

Each session owns an asyncio task running `run_simulation_loop` at
`SIM_FPS = 60`. Every tick:

1. `Simulation.tick_once(DT)` advances physics, weapons, hazards and control
   points, and runs each drone's behavior tree.
2. The session's broadcast callback merges in HIL telemetry and fleet health,
   applies active fault injections, records telemetry, and lets the swarm
   orchestrator re-plan.
3. The state snapshot is sent to every connected WebSocket client and
   published to Redis (`nexusforge:<session_id>`) for multi-server fan-out.

## Components

| Component | Path | Responsibility |
|---|---|---|
| Simulation engine | `simulation/engine/sim.py` | 2D physics in a 1200×900 arena, up to 128 drones, projectiles, hazards, 5 control points, scoring |
| Behavior trees | `agents/behaviors/behavior_tree.py` | Per-drone decisions: attack, evade, regroup, flock, patrol, capture, pincer; aggressive/defensive/flanker profiles |
| Swarm orchestrator | `agents/swarm/orchestrator.py` | Team missions (attack, defend, capture, flank, regroup, scatter, surround, patrol, escort, kamikaze) and formations (wedge, line, circle, spread, diamond, column); auto-tactics every 2 s |
| NLP parser | `agents/nlp/parser.py` | Turns operator text into a `SwarmCommand`; uses Claude when `ANTHROPIC_API_KEY` is set, otherwise a keyword parser |
| RL trainer | `agents/rl/trainer.py` | CPU-only self-play policy training; trained policies plug in as `rl_policy` |
| Edge-AI simulator | `firmware/tinyml/inference.py` | Latency, energy (µJ = mW × ms) and accuracy for 4 models × 5 MCUs × 4/8/16/32-bit quantization |
| HIL manager | `firmware/protocols/hil_mqtt.py` | Simulated ESP32 fleet with noise, drift and packet loss; MQTT topic schema |
| Fault injection | `firmware/fault_injection/injector.py` | 17 fault types and 5 canned scenarios mirroring real ESP32/STM32 failures |
| Telemetry | `backend/telemetry/writer.py` | Batched TimescaleDB writes and a Redis cache; both optional |
| Dashboard | `dashboard/` | Lobby, 2D canvas and lazily-loaded three.js 3D view, HUD, analytics and benchmark pages |
| Firmware | `firmware/esp32_sim/main.cpp` | Real ESP32 sketch (PlatformIO): Wi-Fi, MQTT telemetry, FreeRTOS tasks, inference stub |

## Optional services

Redis, TimescaleDB and Mosquitto are all optional. Without them the backend
runs a single process with in-memory state: Redis fan-out and the telemetry
cache are skipped, and telemetry is not persisted. The headless demo and the
whole test suite need none of them.
