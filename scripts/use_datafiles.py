#!/usr/bin/env python3
import argparse
import os
import shutil
from typing import Dict, List, Tuple

EXPECTED: List[Tuple[str, int]] = [
    ("f_100B.bin", 100),
    ("f_10KB.bin", 10 * 1024),
    ("f_1MB.bin", 1 * 1024 * 1024),
    ("f_10MB.bin", 10 * 1024 * 1024),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-dir", default="DataFiles", help="Directory containing provided files")
    parser.add_argument("--out", default="files", help="Output directory for canonical names")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files in output")
    args = parser.parse_args()

    if not os.path.isdir(args.from_dir):
        raise SystemExit(f"Input directory not found: {args.from_dir}")

    os.makedirs(args.out, exist_ok=True)

    size_to_paths: Dict[int, List[str]] = {}
    for name in os.listdir(args.from_dir):
        p = os.path.join(args.from_dir, name)
        if not os.path.isfile(p):
            continue
        sz = os.path.getsize(p)
        size_to_paths.setdefault(sz, []).append(p)

    for canon_name, expected_size in EXPECTED:
        candidates = size_to_paths.get(expected_size, [])
        if not candidates:
            print(f"Missing file of size {expected_size} bytes for {canon_name}")
            continue
        src = candidates.pop(0)
        dst = os.path.join(args.out, canon_name)
        if os.path.exists(dst) and not args.overwrite:
            print(f"Exists: {dst} (use --overwrite to replace)")
            continue
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst}")


if __name__ == "__main__":
    main()
