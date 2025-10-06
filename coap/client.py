#!/usr/bin/env python3
import argparse
import asyncio
import os
import uuid

import aiocoap

from common.config import Settings
from common.logging_utils import CsvLogger, TransferLogEntry, monotonic_ns


async def run(files, counts, host, port, logger):
    context = await aiocoap.Context.create_client_context()
    for file_name, iterations in counts.items():
        for i in range(1, iterations + 1):
            seq = str(uuid.uuid4())
            uri = f"coap://{host}:{port}/files/{file_name}?seq={seq}&iter={i}"
            t0 = monotonic_ns()
            request = aiocoap.Message(code=aiocoap.GET, uri=uri, mtype=aiocoap.CON)
            response = await context.request(request).response
            payload = bytes(response.payload or b"")
            t1 = monotonic_ns()
            duration_ms = (t1 - t0) / 1e6

            logger.write(
                TransferLogEntry(
                    protocol="coap",
                    role="client",
                    file_name=file_name,
                    file_size_bytes=len(payload),
                    iteration=i,
                    seq_id=seq,
                    qos_or_mode="con-block",
                    t_start_ns=t0,
                    t_end_ns=t1,
                    duration_ms=duration_ms,
                    bytes_sent_sender_to_receiver=len(payload),
                    extra_meta=None,
                )
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-dir", default="files")
    args = parser.parse_args()

    settings = Settings.load()
    host = settings.endpoints.coap_host
    port = settings.endpoints.coap_port

    os.makedirs(os.path.join(settings.log_dir, "coap"), exist_ok=True)
    logger = CsvLogger(os.path.join(settings.log_dir, "coap", "client.csv"))

    counts = settings.counts.to_map()

    try:
        asyncio.run(run(args.files_dir, counts, host, port, logger))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
