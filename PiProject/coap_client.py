#!/usr/bin/env python3
"""
CoAP Client for file transfer experiments (confirmable + block-wise)
Run this on the client machine.
"""

import asyncio
import csv
import os
import sys
import time
from typing import List, Tuple

import aiocoap


class CoAPClientExperiment:
    def __init__(self, server_host: str, server_port: int = 5683):
        # Prefer IPv6 literal if provided; aiocoap handles DNS
        self.server_host = server_host
        self.server_port = server_port
        self.results = []

    async def _get_file_once(self, context: aiocoap.Context, filename: str) -> int:
        uri = f"coap://{self.server_host}:{self.server_port}/file?name={filename}"
        request = aiocoap.Message(code=aiocoap.GET, uri=uri)
        # CON is default; block-wise is automatic. We read whole response.
        response = await context.request(request).response
        if response.code.is_successful():
            return len(response.payload)
        raise RuntimeError(f"CoAP error: {response.code}")

    async def run_transfers(self, files: List[Tuple[str, int]]):
        context = await aiocoap.Context.create_client_context()
        # small delay ensures socket binds before first send
        await asyncio.sleep(0.1)

        for filename, iterations in files:
            file_path = os.path.join("DataFiles", filename)
            if not os.path.exists(file_path):
                print(f"File missing: {file_path}")
                continue
            file_size = os.path.getsize(file_path)
            print(f"Requesting {filename} ({file_size} bytes) {iterations} times")

            for i in range(iterations):
                start = time.time()
                try:
                    received_len = await self._get_file_once(context, filename)
                except Exception as exc:
                    print(f"Iteration {i+1} failed: {exc}")
                    continue
                end = time.time()
                dt = end - start
                throughput = file_size / dt if dt > 0 else 0.0
                self.results.append({
                    "file": filename,
                    "file_size": file_size,
                    "iteration": i + 1,
                    "transfer_time": dt,
                    "throughput": throughput,
                })
                if (i + 1) % 100 == 0 or iterations <= 20:
                    print(f"{filename} iter {i+1}/{iterations}: {dt:.4f}s, {throughput:.2f} B/s")

        await context.shutdown()

    def save_results(self, filename: str = "coap_results.csv"):
        if not self.results:
            print("No results to save.")
            return
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.results[0].keys()))
            writer.writeheader()
            writer.writerows(self.results)
        print(f"Results saved to {filename}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python coap_client.py <server_host> [server_port]", file=sys.stderr)
        print("Example: python coap_client.py 192.168.1.100", file=sys.stderr)
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5683

    # Same experiment loops as MQTT
    files_plan: List[Tuple[str, int]] = [
        ("100B", 10000),
        ("10KB", 1000),
        ("1MB", 100),
        ("10MB", 10),
    ]

    client = CoAPClientExperiment(server_host, server_port)
    try:
        asyncio.run(client.run_transfers(files_plan))
        client.save_results("coap_results.csv")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


