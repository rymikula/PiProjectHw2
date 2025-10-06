#!/usr/bin/env python3
import argparse
import os
import re
import socket
from typing import Optional

import paho.mqtt.client as mqtt

from common.config import Settings
from common.logging_utils import (
    CsvLogger,
    TransferLogEntry,
    monotonic_ns,
    estimate_mqtt_publish_overhead_bytes,
)


TOPIC_RE = re.compile(r"^(.+)/([^/]+)/([0-9a-fA-F-]{36})$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qos", type=int, choices=[1, 2], required=True)
    parser.add_argument("--client-id", default=None)
    args = parser.parse_args()

    settings = Settings.load()
    host = settings.endpoints.broker_host
    port = settings.endpoints.broker_port
    topic_prefix = settings.endpoints.mqtt_topic_prefix.rstrip("/")

    os.makedirs(os.path.join(settings.log_dir, "mqtt"), exist_ok=True)
    log_path = os.path.join(settings.log_dir, "mqtt", f"subscriber_qos{args.qos}.csv")
    logger = CsvLogger(log_path)

    client_id = args.client_id or f"hw3-sub-{socket.gethostname()}-{os.getpid()}"

    def on_connect(client: mqtt.Client, userdata, flags, rc):
        client.subscribe(f"{topic_prefix}/#", qos=args.qos)

    def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        t1 = monotonic_ns()
        m = TOPIC_RE.match(msg.topic)
        file_name: Optional[str] = None
        seq_id: Optional[str] = None
        if m:
            file_name = m.group(2)
            seq_id = m.group(3)
        else:
            parts = msg.topic.split("/")
            if len(parts) >= 3:
                file_name = parts[-2]
                seq_id = parts[-1]
        if file_name is None or seq_id is None:
            return

        payload_len = len(msg.payload or b"")
        bytes_over_sender_to_receiver = estimate_mqtt_publish_overhead_bytes(
            topic=msg.topic, payload_len=payload_len, qos=args.qos
        )

        logger.write(
            TransferLogEntry(
                protocol="mqtt",
                role="subscriber",
                file_name=file_name,
                file_size_bytes=payload_len,
                iteration=0,
                seq_id=seq_id,
                qos_or_mode=f"qos{args.qos}",
                t_start_ns=t1,
                t_end_ns=t1,
                duration_ms=0.0,
                bytes_sent_sender_to_receiver=bytes_over_sender_to_receiver,
                extra_meta={"topic": msg.topic},
            )
        )

    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(host, port, keepalive=60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
