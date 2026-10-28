# Hardware-in-the-loop

Real boards and simulated drones share one arena. A physical ESP32 publishes
telemetry over MQTT and receives commands back; everything else in the
session is simulated.

## MQTT topics

| Topic | Direction | Rate |
|---|---|---|
| `nexusforge/{session}/{drone_id}/telemetry` | board → server | 20 Hz (`TELEMETRY_HZ`) |
| `nexusforge/{session}/{drone_id}/command` | server → board | on demand |

Telemetry is JSON built with ArduinoJson in `firmware/esp32_sim/main.cpp`:
position, power (`battery_pct`, `battery_mv`), compute load and inference
latency.

## Injecting readings over HTTP

Boards or bridges that cannot speak MQTT can post readings directly:

```bash
curl -X POST localhost:8000/sessions/$SID/hil/inject \
  -H 'Content-Type: application/json' \
  -d '{"drone_id": "c83859c3", "battery_pct": 71.5, "pos": {"x": 300, "y": 420}}'
```

Drone IDs are the 8-character ids in `GET /sessions/{sid}` (`drones[].id`).
Each field is optional except `drone_id`; supplied fields override the
simulated drone's state.

## Simulated fleet

`HILManager` (`firmware/protocols/hil_mqtt.py`) models a fleet of ESP32s
without hardware: sensor noise, clock drift, RSSI variance, packet loss and
a battery discharge curve. Fleet health appears in every state broadcast
(`hil_fleet`) and in `GET /sessions/{sid}/telemetry`.

## Fault injection

`FaultInjector` applies faults that mirror real ESP32/STM32 failure modes —
network (packet loss, latency, throttling, MQTT disconnect), power
(drain, brownout, power-off), compute (CPU overload, memory pressure,
corrupted inference, watchdog reset), sensors (GPS drift, IMU bias, frozen
sensor) and swarm-level faults (split brain, command flood, rogue drone).
See the [API reference](api-reference.md#faults).

## Edge-AI model

`firmware/tinyml/inference.py` estimates per-inference latency (with jitter
for cache misses and interrupts), energy and accuracy for each model, MCU
and quantization width. Energy is `power (mW) × latency (ms)`, which is
microjoules. Figures are modelled, not measured on hardware.
