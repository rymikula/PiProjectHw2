#!/usr/bin/env python3
import argparse
import os
import socket
import time
import uuid
from typing import Dict, List

import paho.mqtt.client as mqtt

from common.config import Settings
from common.logging_utils import (
    CsvLogger,
    TransferLogEntry,
    monotonic_ns,
    estimate_mqtt_publish_overhead_bytes,
)
from common.fileset import discover_files_by_size, build_iterations_by_filename


def load_files(files_dir: str, selected: Dict[int, str]) -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    for sz, name in selected.items():
        path = os.path.join(files_dir, name)
        with open(path, "rb") as f:
            files[name] = f.read()
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qos", type=int, choices=[1, 2], required=True)
    parser.add_argument("--files-dir", default="DataFiles")
    parser.add_argument("--client-id", default=None)
    args = parser.parse_args()

    settings = Settings.load()
    host = settings.endpoints.broker_host
    port = settings.endpoints.broker_port
    topic_prefix = settings.endpoints.mqtt_topic_prefix.rstrip("/")

    client_id = args.client_id or f"hw3-pub-{socket.gethostname()}-{os.getpid()}"

    os.makedirs(os.path.join(settings.log_dir, "mqtt"), exist_ok=True)
    log_path = os.path.join(settings.log_dir, "mqtt", f"publisher_qos{args.qos}.csv")
    logger = CsvLogger(log_path)

    selected = discover_files_by_size(args.files_dir)
    if len(selected) < 4:
        raise SystemExit("Expected 4 files in DataFiles with sizes 100B, 10KB, 1MB, 10MB")
    files = load_files(args.files_dir, selected)
    counts_by_name = build_iterations_by_filename(selected, settings.counts.to_map())

    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.connect(host, port, keepalive=60)
    client.loop_start()

    try:
        for file_name, payload in files.items():
            iterations = counts_by_name[file_name]
            for i in range(1, iterations + 1):
                seq = str(uuid.uuid4())
                topic = f"{topic_prefix}/{file_name}/{seq}"
                t0 = monotonic_ns()
                info = client.publish(topic, payload=payload, qos=args.qos, retain=False)
                info.wait_for_publish()
                t1 = monotonic_ns()
                duration_ms = (t1 - t0) / 1e6

                bytes_over_sender_to_receiver = estimate_mqtt_publish_overhead_bytes(
                    topic=topic, payload_len=len(payload), qos=args.qos
                )

                logger.write(
                    TransferLogEntry(
                        protocol="mqtt",
                        role="publisher",
                        file_name=file_name,
                        file_size_bytes=len(payload),
                        iteration=i,
                        seq_id=seq,
                        qos_or_mode=f"qos{args.qos}",
                        t_start_ns=t0,
                        t_end_ns=t1,
                        duration_ms=duration_ms,
                        bytes_sent_sender_to_receiver=bytes_over_sender_to_receiver,
                        extra_meta={"topic": topic},
                    )
                )
                if i % 100 == 0:
                    time.sleep(0.01)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
