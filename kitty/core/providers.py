"""Provider directory helpers."""

from __future__ import annotations

from pathlib import Path

from .config import load_global_config, resolve_provider_path


def get_provider_paths() -> dict[str, Path]:
    cfg = load_global_config()
    providers = cfg.get("providers", {})
    result: dict[str, Path] = {}
    for name, raw_path in providers.items():
        if not isinstance(raw_path, str):
            continue
        result[name] = resolve_provider_path(raw_path)
    return result


def get_provider_skill_paths(skill: str) -> dict[str, Path]:
    return {name: path / skill for name, path in get_provider_paths().items()}
