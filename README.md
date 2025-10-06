## CSC 591/791, ECE592 — HW3: MQTT vs CoAP vs HTTP File Transfer

This project provides runnable reference implementations to transfer files using MQTT (QoS 1 and 2), CoAP (confirmable + blockwise), and HTTP, while measuring per-transfer latency and throughput and estimating application-layer overhead from sender to receiver.

### Quick Start

- **Use your provided DataFiles directly**
Place the four provided files in `DataFiles/` (already present) and ensure they are exactly these sizes:
- ~100 bytes
- ~10 KiB
- ~1 MiB
- ~10 MiB
The code auto-discovers them by size and uses their actual filenames.

- **Install dependencies**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
Note: `uvloop` was removed to avoid build failures on Python 3.13; no functionality depends on it.

- **Configure addresses** (create/edit `.env`)
```bash
cp .env.example .env  # if present, otherwise create .env with the same keys
```
Vars: `BROKER_HOST`, `BROKER_PORT`, `COAP_HOST`, `COAP_PORT`, `HTTP_HOST`, `HTTP_PORT`.

- **MQTT experiments**
Broker (e.g., Mosquitto): `mosquitto -p 1883`
Subscriber (leave running in a separate shell):
```bash
python -m mqtt.subscriber --qos 1
python -m mqtt.subscriber --qos 2
```
Publisher (reads from DataFiles by default):
```bash
python -m mqtt.publisher --qos 1
python -m mqtt.publisher --qos 2
```
Logs: `logs/mqtt/`.

- **CoAP experiments**
Server (serves from DataFiles):
```bash
python -m coap.server
```
Client (requests discovered filenames):
```bash
python -m coap.client
```

- **HTTP experiments**
Server (serves from DataFiles):
```bash
python -m http_proto.server
```
Client (requests discovered filenames):
```bash
python -m http_proto.client
```

- **Aggregate to Excel**
```bash
python -m tools.aggregate_results --out "results/Results File.xlsx"
```

If you prefer direct script paths, set `PYTHONPATH=.` before the command, e.g.:
```bash
PYTHONPATH=. python3 mqtt/publisher.py --qos 1
```

### Notes
- Overhead excludes reverse-direction control traffic per assignment.
- For MQTT, sender→receiver counts publisher→broker plus broker→subscriber PUBLISH bytes.
- Sync clocks (NTP) for best cross-device timing.
- Python 3.10+ recommended.
