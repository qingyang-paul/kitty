"""Hash helpers for skill directories."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_directory(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        raise ValueError(f"{path} is not a directory.")

    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path)
        digest.update(str(relative).encode())
        if item.is_file():
            digest.update(item.read_bytes())
    return digest.hexdigest()
