#!/usr/bin/env python3
import argparse
import os
import uuid
import requests

from common.config import Settings
from common.logging_utils import CsvLogger, TransferLogEntry, monotonic_ns


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-dir", default="files")
    args = parser.parse_args()

    settings = Settings.load()
    host = settings.endpoints.http_host
    port = settings.endpoints.http_port

    os.makedirs(os.path.join(settings.log_dir, "http"), exist_ok=True)
    logger = CsvLogger(os.path.join(settings.log_dir, "http", "client.csv"))

    counts = settings.counts.to_map()

    session = requests.Session()

    for file_name, iterations in counts.items():
        for i in range(1, iterations + 1):
            seq = str(uuid.uuid4())
            url = f"http://{host}:{port}/files/{file_name}?seq={seq}&iter={i}"
            t0 = monotonic_ns()
            r = session.get(url)
            r.raise_for_status()
            _ = r.content
            t1 = monotonic_ns()
            duration_ms = (t1 - t0) / 1e6

            logger.write(
                TransferLogEntry(
                    protocol="http",
                    role="client",
                    file_name=file_name,
                    file_size_bytes=len(_),
                    iteration=i,
                    seq_id=seq,
                    qos_or_mode="http",
                    t_start_ns=t0,
                    t_end_ns=t1,
                    duration_ms=duration_ms,
                    bytes_sent_sender_to_receiver=len(_),
                    extra_meta=None,
                )
            )
            if i % 100 == 0:
                pass


if __name__ == "__main__":
    main()
