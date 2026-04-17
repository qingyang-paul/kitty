"""Provider path resolution for a workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import load_global_config, load_workspace_config


def get_provider_paths(workspace: Path) -> dict[str, Path]:
    """
    Return {provider_name: resolved_skills_dir} for the workspace.
    Paths are deduplicated by resolved absolute path.
    """
    global_cfg = load_global_config()
    ws_cfg = load_workspace_config(workspace)

    # Workspace can override which providers are active
    active_providers: list[str] = ws_cfg.get("providers", global_cfg.get("default_providers", []))

    all_provider_defs: dict[str, str] = global_cfg.get("providers", {})

    result: dict[str, Path] = {}
    for name in active_providers:
        raw = all_provider_defs.get(name)
        if raw is None:
            continue
        if raw.startswith("~/") or raw.startswith("~\\"):
            # Home-relative: ~/.claude/skills → /Users/x/.claude/skills
            p = Path.home() / raw[2:]
        elif raw.startswith("/"):
            p = Path(raw)
        else:
            # Workspace-relative: .claude/skills → /project/.claude/skills
            p = workspace / raw
        result[name] = p

    return result


def unique_provider_paths(workspace: Path) -> list[Path]:
    """Return deduplicated list of provider skills directories."""
    seen: set[Path] = set()
    result: list[Path] = []
    for p in get_provider_paths(workspace).values():
        resolved = p.resolve() if p.exists() else p
        if resolved not in seen:
            seen.add(resolved)
            result.append(p)
    return result


def skill_link_paths(workspace: Path, skill: str, provider: Optional[str] = None) -> list[tuple[str, Path]]:
    """
    Return list of (provider_name, link_path) for a skill in the workspace.
    If provider is specified, return only that provider's path.
    Deduplicates by resolved destination path.
    """
    paths = get_provider_paths(workspace)
    if provider:
        if provider not in paths:
            raise ValueError(f"Unknown provider '{provider}'. Known: {list(paths)}")
        return [(provider, paths[provider] / skill)]

    seen_targets: set[str] = set()
    result: list[tuple[str, Path]] = []
    for name, skills_dir in paths.items():
        link = skills_dir / skill
        # Deduplicate by the string path (before resolution)
        key = str(skills_dir / skill)
        if key not in seen_targets:
            seen_targets.add(key)
            result.append((name, link))
    return result
