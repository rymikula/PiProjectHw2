#!/usr/bin/env python3
import argparse
import asyncio
import os
import uuid
from typing import Optional

import aiocoap.resource as resource
import aiocoap
from urllib.parse import parse_qs

from common.config import Settings
from common.logging_utils import CsvLogger, TransferLogEntry, monotonic_ns


def estimate_coap_response_bytes(payload_len: int, token_len: int, has_block2: bool) -> int:
    # Very rough estimate: 4 bytes base header + token + minimal options + payload marker if any + payload
    # Blockwise adds a Block2 option ~ 1-3 bytes typically; we'll assume +2
    base = 4 + token_len
    options = 2 if has_block2 else 0
    payload_marker = 1 if payload_len > 0 else 0
    return base + options + payload_marker + payload_len


class FileResource(resource.Resource):
    def __init__(self, files_dir: str, logger: CsvLogger):
        super().__init__()
        self.files_dir = files_dir
        self.logger = logger

    async def render_get(self, request):
        # Path: files/{name}
        if not request.opt.uri_path or len(request.opt.uri_path) != 2 or request.opt.uri_path[0] != 'files':
            return aiocoap.Message(code=aiocoap.NOT_FOUND)
        file_name = request.opt.uri_path[1]
        path = os.path.join(self.files_dir, file_name)
        if not os.path.exists(path):
            return aiocoap.Message(code=aiocoap.NOT_FOUND)

        qs = request.opt.uri_query or []
        qmap = {}
        for q in qs:
            k, _, v = q.partition('=')
            if k:
                qmap.setdefault(k, []).append(v)
        seq = (qmap.get('seq', [str(uuid.uuid4())])[0])
        iteration = int(qmap.get('iter', ['0'])[0])

        with open(path, 'rb') as f:
            payload = f.read()

        t0 = monotonic_ns()
        msg = aiocoap.Message(code=aiocoap.CONTENT, payload=payload)
        t1 = monotonic_ns()
        duration_ms = (t1 - t0) / 1e6

        # We cannot know blockwise slicing here; approximate as single response
        token_len = len(request.token or b"")
        est_bytes = estimate_coap_response_bytes(len(payload), token_len, has_block2=False)

        self.logger.write(
            TransferLogEntry(
                protocol="coap",
                role="server",
                file_name=file_name,
                file_size_bytes=len(payload),
                iteration=iteration,
                seq_id=seq,
                qos_or_mode="con-block",
                t_start_ns=t0,
                t_end_ns=t1,
                duration_ms=duration_ms,
                bytes_sent_sender_to_receiver=est_bytes,
                extra_meta=None,
            )
        )
        return msg


async def main_async(files_dir: str, host: str, port: int, logger: CsvLogger):
    root = resource.Site()
    root.add_resource(['files'], resource.PathCapable())
    root.add_resource(['files', resource.AnyPath()], FileResource(files_dir, logger))

    await aiocoap.Context.create_server_context(root, bind=(host, port))
    await asyncio.get_running_loop().create_future()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-dir", default="files")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    settings = Settings.load()
    host = args.host or settings.endpoints.coap_host
    port = args.port or settings.endpoints.coap_port

    os.makedirs(os.path.join(settings.log_dir, "coap"), exist_ok=True)
    logger = CsvLogger(os.path.join(settings.log_dir, "coap", "server.csv"))

    try:
        asyncio.run(main_async(args.files_dir, host, port, logger))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
