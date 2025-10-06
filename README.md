## CSC 591/791, ECE592 — HW3: MQTT vs CoAP vs HTTP File Transfer

This project provides runnable reference implementations to transfer files using MQTT (QoS 1 and 2), CoAP (confirmable + blockwise), and HTTP, while measuring per-transfer latency and throughput and estimating application-layer overhead from sender to receiver.

### Quick Start

- **0) Create the 4 files**
```bash
python3 scripts/generate_files.py --out files
```
Creates:
- `files/f_100B.bin` (~100 bytes)
- `files/f_10KB.bin` (~10 KiB)
- `files/f_1MB.bin` (~1 MiB)
- `files/f_10MB.bin` (~10 MiB)

- **1) Install dependencies**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

- **2) Configure addresses** (edit `.env`)
```bash
cp .env.example .env
```
Vars: `BROKER_HOST`, `BROKER_PORT`, `COAP_HOST`, `COAP_PORT`, `HTTP_HOST`, `HTTP_PORT`.

- **3) MQTT experiments**
Broker (e.g., Mosquitto): `mosquitto -p 1883`
Publisher:
```bash
python3 mqtt/publisher.py --qos 1 --files-dir files
python3 mqtt/publisher.py --qos 2 --files-dir files
```
Subscriber:
```bash
python3 mqtt/subscriber.py --qos 1
python3 mqtt/subscriber.py --qos 2
```
Logs: `logs/mqtt/`.

- **4) CoAP experiments**
Server:
```bash
python3 coap/server.py --files-dir files
```
Client:
```bash
python3 coap/client.py --files-dir files
```

- **5) HTTP experiments**
Server:
```bash
python3 http/server.py --files-dir files
```
Client:
```bash
python3 http/client.py --files-dir files
```

- **6) Aggregate to Excel**
```bash
python3 tools/aggregate_results.py --out "results/Results File.xlsx"
```

### Notes
- Overhead excludes reverse-direction control traffic per assignment.
- For MQTT, sender→receiver counts publisher→broker plus broker→subscriber PUBLISH bytes.
- Sync clocks (NTP) for best cross-device timing.
- Python 3.10+ recommended.
