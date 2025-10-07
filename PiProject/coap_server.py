#!/usr/bin/env python3
"""
CoAP Server for file transfer experiments (confirmable + block-wise)
Run this on the server machine.
"""

import asyncio
import os
import sys
from urllib.parse import parse_qs

import aiocoap.resource as resource
import aiocoap


class FileResource(resource.Resource):
    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        # Expect query ?name=<filename>
        query = request.opt.uri_query or []
        params = parse_qs("&".join(query)) if query else {}
        names = params.get("name", [])
        if not names:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"missing name parameter")

        filename = names[0]
        safe_name = os.path.basename(filename)
        file_path = os.path.join(self.base_dir, safe_name)

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return aiocoap.Message(code=aiocoap.NOT_FOUND, payload=b"file not found")

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception as exc:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, payload=str(exc).encode())

        # Content-Format: application/octet-stream, block-wise handled by aiocoap automatically
        response = aiocoap.Message(code=aiocoap.CONTENT, payload=data)
        response.opt.content_format = 42  # application/octet-stream
        return response


async def main():
    if len(sys.argv) > 2:
        print("Usage: python coap_server.py [listen_host]", file=sys.stderr)
        sys.exit(1)

    listen_host = sys.argv[1] if len(sys.argv) == 2 else None  # None means all interfaces
    site = resource.Site()

    data_dir = "DataFiles"
    site.add_resource(["file"], FileResource(data_dir))

    bind = (listen_host or "::", 5683)
    context = await aiocoap.Context.create_server_context(site, bind=bind)

    print(f"CoAP server listening on {bind[0]}:{bind[1]} serving from {data_dir}")
    await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


