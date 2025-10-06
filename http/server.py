#!/usr/bin/env python3
import argparse
import os
import socket
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from common.config import Settings
from common.logging_utils import CsvLogger, TransferLogEntry, monotonic_ns


class FileHandler(BaseHTTPRequestHandler):
    server_version = "HW3HTTP/1.0"

    def do_GET(self):
        settings: Settings = self.server.settings  # type: ignore[attr-defined]
        files_dir = self.server.files_dir  # type: ignore[attr-defined]
        logger: CsvLogger = self.server.logger  # type: ignore[attr-defined]

        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if len(parts) != 2 or parts[0] != "files":
            self.send_error(404, "Not Found")
            return

        file_name = parts[1]
        path = os.path.join(files_dir, file_name)
        if not os.path.exists(path):
            self.send_error(404, "Not Found")
            return

        qs = parse_qs(parsed.query or "")
        seq = (qs.get("seq", [str(uuid.uuid4())])[0])
        iteration = int(qs.get("iter", ["0"])[0])

        with open(path, "rb") as f:
            payload = f.read()

        t0 = monotonic_ns()
        # Build headers
        body = payload
        body_len = len(body)
        self.send_response(200, "OK")
        # Minimal headers to be consistent
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(body_len))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()
        t1 = monotonic_ns()
        duration_ms = (t1 - t0) / 1e6

        # Approximate bytes sender->receiver at app layer: status line + headers + CRLFs + body
        status_line = f"HTTP/1.0 200 OK\r\n"
        headers = [
            f"Server: {self.server_version}\r\n",
            "Date: -\r\n",
            "Content-Type: application/octet-stream\r\n",
            f"Content-Length: {body_len}\r\n",
        ]
        header_bytes = len(status_line) + sum(len(h) for h in headers) + len("\r\n")
        total_bytes = header_bytes + body_len

        logger.write(
            TransferLogEntry(
                protocol="http",
                role="server",
                file_name=file_name,
                file_size_bytes=body_len,
                iteration=iteration,
                seq_id=seq,
                qos_or_mode="http",
                t_start_ns=t0,
                t_end_ns=t1,
                duration_ms=duration_ms,
                bytes_sent_sender_to_receiver=total_bytes,
                extra_meta=None,
            )
        )

    def log_message(self, format, *args):
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-dir", default="files")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    settings = Settings.load()
    host = args.host or settings.endpoints.http_host
    port = args.port or settings.endpoints.http_port

    os.makedirs(os.path.join(settings.log_dir, "http"), exist_ok=True)
    logger = CsvLogger(os.path.join(settings.log_dir, "http", "server.csv"))

    httpd = HTTPServer((host, port), FileHandler)
    httpd.settings = settings  # type: ignore[attr-defined]
    httpd.files_dir = args.files_dir  # type: ignore[attr-defined]
    httpd.logger = logger  # type: ignore[attr-defined]

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
