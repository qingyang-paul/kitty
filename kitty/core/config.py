"""Config loading/saving for ~/.kitty/config.json and workspace .kitty/config.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

KITTY_HOME = Path.home() / ".kitty"
GLOBAL_CONFIG = KITTY_HOME / "config.json"

DEFAULT_GLOBAL_CONFIG: dict[str, Any] = {
    "version": 1,
    "remote": None,
    "providers": {
        "claude": ".claude/skills",
        "gemini": ".agents/skills",
        "codex": ".agents/skills",
    },
    "default_providers": ["claude", "gemini"],
    "commit_author": {"name": "kitty", "email": "kitty@local"},
}

DEFAULT_KITTYIGNORE = """\
# Kitty default ignore rules
*.pyc
__pycache__/
.DS_Store
*.log
node_modules/
.env
*.tmp
.kitty/
"""

DEFAULT_SKILL_MD = """\
---
name: {skill}
description: >
  TODO: describe this skill
---

# {skill}

TODO: write skill instructions.
"""


def load_global_config() -> dict[str, Any]:
    if not GLOBAL_CONFIG.exists():
        return dict(DEFAULT_GLOBAL_CONFIG)
    with open(GLOBAL_CONFIG) as f:
        data = json.load(f)
    # Merge with defaults so new keys are always present
    merged = dict(DEFAULT_GLOBAL_CONFIG)
    merged.update(data)
    return merged


def save_global_config(cfg: dict[str, Any]) -> None:
    KITTY_HOME.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def load_workspace_config(workspace: Path) -> dict[str, Any]:
    path = workspace / ".kitty" / "config.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_workspace_config(workspace: Path, cfg: dict[str, Any]) -> None:
    (workspace / ".kitty").mkdir(parents=True, exist_ok=True)
    path = workspace / ".kitty" / "config.json"
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def has_remote() -> bool:
    cfg = load_global_config()
    return bool(cfg.get("remote"))


def find_workspace_root(cwd: Path | None = None) -> Path:
    """Find workspace root: git repo root, or cwd as fallback."""
    import subprocess

    start = cwd or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return start
