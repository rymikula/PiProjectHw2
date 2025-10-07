#!/usr/bin/env python3
"""
HTTP Server for file transfer experiments
Run this on the server machine.
Serves files from the DataFiles directory at GET /file?name=<filename>
"""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


DATA_DIR = "DataFiles"


class FileRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/file":
            self.send_error(404, "Not found")
            return

        params = parse_qs(parsed.query or "")
        names = params.get("name", [])
        if not names:
            self.send_error(400, "Missing 'name' parameter")
            return

        filename = os.path.basename(names[0])
        file_path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return

        try:
            file_size = os.path.getsize(file_path)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(file_size))
            self.end_headers()

            with open(file_path, "rb") as f:
                # Stream the file in chunks to the client
                chunk_size = 64 * 1024
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except BrokenPipeError:
            # Client closed connection early; nothing to do
            pass
        except Exception as exc:
            # If headers not sent, send 500; otherwise just stop
            try:
                if not self.headers_sent:
                    self.send_error(500, f"Server error: {exc}")
            except Exception:
                pass

    # Avoid default noisy logging for each request
    def log_message(self, format, *args):
        return


def main():
    host = "0.0.0.0"
    port = 8000
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])

    if not os.path.isdir(DATA_DIR):
        print(f"Warning: '{DATA_DIR}' directory not found in working directory.")

    server = HTTPServer((host, port), FileRequestHandler)
    print(f"HTTP server listening on {host}:{port}, serving from {DATA_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()


