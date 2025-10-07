#!/usr/bin/env python3
"""
HTTP Client for file transfer experiments
Run this on the client machine.
"""

import csv
import os
import sys
import time
from typing import List, Tuple

import urllib.request
import urllib.error
import urllib.parse


class HTTPClientExperiment:
    def __init__(self, server_host: str, server_port: int = 8000):
        self.server_host = server_host
        self.server_port = server_port
        self.results = []

    def _get_file_once(self, filename: str) -> int:
        query = urllib.parse.urlencode({"name": filename})
        url = f"http://{self.server_host}:{self.server_port}/file?{query}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            # Read all bytes to ensure full transfer
            data = resp.read()
            return len(data)

    def run_transfers(self, files: List[Tuple[str, int]]):
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
                    received_len = self._get_file_once(filename)
                except (urllib.error.HTTPError, urllib.error.URLError) as exc:
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

    def save_results(self, filename: str = "http_results.csv"):
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
        print("Usage: python http_client.py <server_host> [server_port]", file=sys.stderr)
        print("Example: python http_client.py 192.168.1.100", file=sys.stderr)
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000

    files_plan: List[Tuple[str, int]] = [
        ("100B", 10000),
        ("10KB", 1000),
        ("1MB", 100),
        ("10MB", 10),
    ]

    client = HTTPClientExperiment(server_host, server_port)
    try:
        client.run_transfers(files_plan)
        client.save_results("http_results.csv")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


