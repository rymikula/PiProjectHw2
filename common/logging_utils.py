import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TransferLogEntry:
    protocol: str
    role: str  # publisher|subscriber|client|server
    file_name: str
    file_size_bytes: int
    iteration: int
    seq_id: str
    qos_or_mode: str  # e.g., qos1, qos2, coap-con, http
    t_start_ns: int
    t_end_ns: int
    duration_ms: float
    bytes_sent_sender_to_receiver: int  # app-layer bytes counted on sender->receiver path only
    extra_meta: Optional[Dict[str, str]] = None


class CsvLogger:
    def __init__(self, log_path: str) -> None:
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "protocol",
                        "role",
                        "file_name",
                        "file_size_bytes",
                        "iteration",
                        "seq_id",
                        "qos_or_mode",
                        "t_start_ns",
                        "t_end_ns",
                        "duration_ms",
                        "bytes_sent_sender_to_receiver",
                        "extra_meta_json",
                    ]
                )

    def write(self, entry: TransferLogEntry) -> None:
        import json

        with open(self.log_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    entry.protocol,
                    entry.role,
                    entry.file_name,
                    entry.file_size_bytes,
                    entry.iteration,
                    entry.seq_id,
                    entry.qos_or_mode,
                    entry.t_start_ns,
                    entry.t_end_ns,
                    f"{entry.duration_ms:.3f}",
                    entry.bytes_sent_sender_to_receiver,
                    json.dumps(entry.extra_meta or {}, separators=(",", ":")),
                ]
            )


def monotonic_ns() -> int:
    return time.monotonic_ns()


def estimate_mqtt_publish_overhead_bytes(topic: str, payload_len: int, qos: int) -> int:
    # MQTT v3.1.1 PUBLISH header estimation: Fixed header + variable header + topic length
    # Fixed header: 2+ bytes (remaining length varint). We'll estimate conservatively.
    # Variable header: topic length (2 bytes) + topic + (QoS>0) packet identifier (2 bytes)
    remaining_len = 2 + len(topic) + (2 if qos > 0 else 0) + payload_len
    # Remaining length field is 1-4 bytes depending on size
    if remaining_len < 128:
        rem_len_len = 1
    elif remaining_len < 16384:
        rem_len_len = 2
    elif remaining_len < 2097152:
        rem_len_len = 3
    else:
        rem_len_len = 4
    fixed_header = 1 + rem_len_len
    variable_header = 2 + len(topic) + (2 if qos > 0 else 0)
    return fixed_header + variable_header + payload_len
