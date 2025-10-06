#!/usr/bin/env python3
import argparse
import os
import secrets

SPECS = [
    ("f_100B.bin", 100),
    ("f_10KB.bin", 10 * 1024),
    ("f_1MB.bin", 1 * 1024 * 1024),
    ("f_10MB.bin", 10 * 1024 * 1024),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="files", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    for name, size in SPECS:
        path = os.path.join(args.out, name)
        if os.path.exists(path) and os.path.getsize(path) == size:
            print(f"Exists and sized: {path} ({size} bytes)")
            continue
        print(f"Writing {path} ({size} bytes)...")
        with open(path, "wb") as f:
            chunk = 1024 * 1024
            remaining = size
            while remaining > 0:
                n = min(chunk, remaining)
                f.write(secrets.token_bytes(n))
                remaining -= n


if __name__ == "__main__":
    main()
