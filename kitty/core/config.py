"""Global config and filesystem layout helpers for kitty."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_KITTY_HOME = Path.home() / ".kitty"
_KITTY_HOME_OVERRIDE: Path | None = None

DEFAULT_GLOBAL_CONFIG: dict[str, Any] = {
    "version": 1,
    "providers": {
        "claude": "~/.claude/skills",
        "agents": "~/.agents/skills",
        "codex": "~/.codex/skills",
    },
    "default_editor": "typora",
}

DEFAULT_MANIFEST: dict[str, Any] = {"skills": {}}

DEFAULT_KITTYIGNORE = """\
# Kitty default ignore rules
*.pyc
__pycache__/
.DS_Store
*.log
node_modules/
.env
*.tmp
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


def set_kitty_home(path: Path | None) -> None:
    global _KITTY_HOME_OVERRIDE
    if path is None:
        _KITTY_HOME_OVERRIDE = None
        return
    _KITTY_HOME_OVERRIDE = path.expanduser().resolve()


def get_kitty_home() -> Path:
    if _KITTY_HOME_OVERRIDE is not None:
        return _KITTY_HOME_OVERRIDE
    raw = os.getenv("KITTY_WORKSPACE")
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_KITTY_HOME


def get_global_config_path() -> Path:
    return get_kitty_home() / "config.json"


def get_manifest_path() -> Path:
    return get_kitty_home() / "manifest.yaml"


def get_skills_dir() -> Path:
    return get_kitty_home() / "skills"


def get_kittyignore_path() -> Path:
    return get_kitty_home() / ".kittyignore"


def resolve_provider_path(raw: str) -> Path:
    if raw.startswith("~/") or raw.startswith("~\\"):
        return Path.home() / raw[2:]
    if raw.startswith("/"):
        return Path(raw)
    return Path.home() / raw


def load_global_config() -> dict[str, Any]:
    cfg_path = get_global_config_path()
    if not cfg_path.exists():
        return json.loads(json.dumps(DEFAULT_GLOBAL_CONFIG))
    with open(cfg_path) as f:
        data = json.load(f)
    merged = json.loads(json.dumps(DEFAULT_GLOBAL_CONFIG))
    merged.update(data)
    merged_providers = dict(DEFAULT_GLOBAL_CONFIG["providers"])
    merged_providers.update(data.get("providers", {}))
    merged["providers"] = merged_providers
    return merged


def save_global_config(cfg: dict[str, Any]) -> None:
    kitty_home = get_kitty_home()
    kitty_home.mkdir(parents=True, exist_ok=True)
    with open(get_global_config_path(), "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def load_manifest() -> dict[str, Any]:
    path = get_manifest_path()
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_MANIFEST))
    text = path.read_text().strip()
    if not text:
        return json.loads(json.dumps(DEFAULT_MANIFEST))
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        if text.replace(" ", "") in {"skills:{}", "skills:{}\n"}:
            return json.loads(json.dumps(DEFAULT_MANIFEST))
        raise ValueError(f"Invalid manifest format at {path}.")
    if not isinstance(data, dict):
        return json.loads(json.dumps(DEFAULT_MANIFEST))
    skills = data.get("skills")
    if not isinstance(skills, dict):
        data["skills"] = {}
    return data


def save_manifest(manifest: dict[str, Any]) -> None:
    kitty_home = get_kitty_home()
    kitty_home.mkdir(parents=True, exist_ok=True)
    with open(get_manifest_path(), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def is_initialized() -> bool:
    kitty_home = get_kitty_home()
    return (
        kitty_home.is_dir()
        and get_skills_dir().is_dir()
        and get_global_config_path().is_file()
        and get_manifest_path().is_file()
        and get_kittyignore_path().is_file()
    )


def ensure_global_workspace() -> list[str]:
    created: list[str] = []
    kitty_home = get_kitty_home()
    kitty_home.mkdir(parents=True, exist_ok=True)

    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        skills_dir.mkdir(parents=True, exist_ok=True)
        created.append(str(skills_dir))

    cfg_path = get_global_config_path()
    if not cfg_path.exists():
        save_global_config(DEFAULT_GLOBAL_CONFIG)
        created.append(str(cfg_path))

    manifest_path = get_manifest_path()
    if not manifest_path.exists():
        save_manifest(DEFAULT_MANIFEST)
        created.append(str(manifest_path))

    kittyignore_path = get_kittyignore_path()
    if not kittyignore_path.exists():
        kittyignore_path.write_text(DEFAULT_KITTYIGNORE)
        created.append(str(kittyignore_path))

    cfg = load_global_config()
    providers = cfg.get("providers", {})
    for provider_path_raw in providers.values():
        provider_path = resolve_provider_path(provider_path_raw)
        if not provider_path.exists():
            provider_path.mkdir(parents=True, exist_ok=True)
            created.append(str(provider_path))

    return created
