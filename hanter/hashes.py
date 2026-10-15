"""SHA-256 chain-of-custody manifest."""
import hashlib
import os
from typing import Dict, List


def sha256_file(path):
    # type: (str) -> str
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(paths):
    # type: (List[str]) -> List[Dict]
    rows = []
    for p in sorted(paths):
        rows.append({
            "path": p,
            "bytes": os.path.getsize(p),
            "sha256": sha256_file(p),
        })
    return rows


def collect_files(root, exts=None):
    # type: (str, object) -> List[str]
    out = []
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            if exts and not fn.lower().endswith(exts):
                continue
            out.append(os.path.join(dp, fn))
    return sorted(out)
