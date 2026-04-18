"""kitty status"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click

from ..core.config import ensure_global_workspace, get_skills_dir, load_manifest
from ..core.hashing import hash_directory
from ..core.providers import get_provider_skill_paths, get_provider_paths


def _provider_state(skill: str, canonical_hash: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for provider_name, skill_path in get_provider_skill_paths(skill).items():
        if not skill_path.exists():
            result[provider_name] = "missing"
            continue
        if not skill_path.is_dir():
            result[provider_name] = "invalid"
            continue
        provider_hash = hash_directory(skill_path)
        if provider_hash == canonical_hash:
            result[provider_name] = "synced"
        else:
            result[provider_name] = "changed"
    return result


def _latest_modified_at(path: Path) -> str:
    latest = path.stat().st_mtime
    for item in path.rglob("*"):
        mtime = item.stat().st_mtime
        if mtime > latest:
            latest = mtime
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S")


@click.command("status")
def cmd_status() -> None:
    """Show whether skills are modified and whether providers are in sync."""
    ensure_global_workspace()

    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        click.echo("No skills yet.")
        return

    skills = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
    if not skills:
        click.echo("No skills yet.")
        return

    manifest = load_manifest()
    skill_meta = manifest.get("skills", {})
    provider_names = list(get_provider_paths().keys())

    header = ["SKILL", "SYNCED", "PENDING_SYNC", "LAST_MODIFIED"] + [name.upper() for name in provider_names]
    click.echo("  ".join(f"{name:<20}" for name in header))
    click.echo("-" * (22 * len(header)))

    for skill_name in skills:
        canonical_dir = skills_dir / skill_name
        if not canonical_dir.is_dir():
            continue

        canonical_hash = hash_directory(canonical_dir)
        manifest_entry = skill_meta.get(skill_name, {})
        last_distributed_hash = manifest_entry.get("last_distributed_hash")
        if not last_distributed_hash:
            pending_sync = "yes"
        else:
            pending_sync = "yes" if last_distributed_hash != canonical_hash else "no"

        provider_states = _provider_state(skill_name, canonical_hash)
        synced = "yes" if provider_states and all(v == "synced" for v in provider_states.values()) else "no"
        last_modified = _latest_modified_at(canonical_dir)

        row = [skill_name, synced, pending_sync, last_modified]
        row.extend(provider_states.get(provider_name, "missing") for provider_name in provider_names)
        click.echo("  ".join(f"{cell:<20}" for cell in row))
