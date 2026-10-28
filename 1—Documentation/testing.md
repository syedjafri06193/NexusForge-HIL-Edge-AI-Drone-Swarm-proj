# Testing

```bash
pip install -r backend/requirements.txt pytest
pytest
```

| Suite | Path | Covers |
|---|---|---|
| Simulation | `tests/simulation/` | Physics, collisions, weapons, hazards, control points, scoring |
| Agents | `tests/agents/` | Behavior-tree nodes and profiles, swarm missions and formations, NLP parsing |
| Firmware / edge AI | `tests/backend/test_firmware.py` | Inference model (including energy units), HIL fleet, fault injection |
| API | `tests/api/` | Session lifecycle and limits, input validation, HIL inject, WebSocket robustness |

None of the tests need Redis, TimescaleDB or MQTT.

CI (`.github/workflows/ci.yml`) runs ruff (syntax errors and pyflakes), the
test suite and the headless demo on Python 3.11 and 3.12, and type-checks
and builds the dashboard.
