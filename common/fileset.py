import os
from typing import Dict, List, Tuple

EXPECTED_SIZES: List[int] = [
    100,
    10 * 1024,
    1 * 1024 * 1024,
    10 * 1024 * 1024,
]


def discover_files_by_size(files_dir: str) -> Dict[int, str]:
    """Return a mapping size_bytes -> filename for the four expected sizes.
    Picks the first (alphabetically) file that exactly matches each size.
    """
    size_to_names: Dict[int, List[str]] = {}
    for name in sorted(os.listdir(files_dir)):
        path = os.path.join(files_dir, name)
        if not os.path.isfile(path):
            continue
        sz = os.path.getsize(path)
        if sz in EXPECTED_SIZES:
            size_to_names.setdefault(sz, []).append(name)
    selected: Dict[int, str] = {}
    for sz in EXPECTED_SIZES:
        names = size_to_names.get(sz, [])
        if names:
            selected[sz] = names[0]
    return selected


def build_iterations_by_filename(size_to_name: Dict[int, str], counts_map: Dict[str, int]) -> Dict[str, int]:
    """Map discovered filenames to iteration counts based on size bucket.
    counts_map keys are canonical labels: 'f_100B.bin', 'f_10KB.bin', 'f_1MB.bin', 'f_10MB.bin'.
    """
    size_to_count: Dict[int, int] = {
        100: counts_map.get("f_100B.bin", 0),
        10 * 1024: counts_map.get("f_10KB.bin", 0),
        1 * 1024 * 1024: counts_map.get("f_1MB.bin", 0),
        10 * 1024 * 1024: counts_map.get("f_10MB.bin", 0),
    }
    name_to_iters: Dict[str, int] = {}
    for sz, name in size_to_name.items():
        iters = size_to_count.get(sz, 0)
        if iters > 0:
            name_to_iters[name] = iters
    return name_to_iters
