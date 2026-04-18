"""kitty distribute <skill>"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import click

from ..core.config import ensure_global_workspace, get_skills_dir, load_manifest, save_manifest
from ..core.hashing import hash_directory
from ..core.params import complete_skill_names
from ..core.providers import get_provider_skill_paths


def _replace_with_copy(source_dir: Path, target_dir: Path) -> None:
    if target_dir.is_symlink() or target_dir.is_file():
        target_dir.unlink()
    elif target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)


@click.command("distribute")
@click.argument("skill", type=click.STRING, shell_complete=complete_skill_names)
def cmd_distribute(skill: str) -> None:
    """Copy one skill from ~/.kitty/skills to all provider skill directories."""
    ensure_global_workspace()

    canonical_dir = get_skills_dir() / skill
    if not canonical_dir.exists():
        click.echo(f"Skill '{skill}' not found in {get_skills_dir()}.", err=True)
        raise SystemExit(1)

    if not canonical_dir.is_dir():
        click.echo(f"Skill '{skill}' path is not a directory: {canonical_dir}", err=True)
        raise SystemExit(1)

    canonical_hash = hash_directory(canonical_dir)
    provider_hashes: dict[str, str] = {}

    click.echo(f"Distributing '{skill}' from {canonical_dir}")
    for provider_name, provider_skill_dir in get_provider_skill_paths(skill).items():
        provider_skill_dir.parent.mkdir(parents=True, exist_ok=True)
        _replace_with_copy(canonical_dir, provider_skill_dir)
        provider_hashes[provider_name] = hash_directory(provider_skill_dir)
        click.echo(f"  - {provider_name}: copied to {provider_skill_dir}")

    manifest = load_manifest()
    skills_meta = manifest.setdefault("skills", {})
    providers_meta = {}
    for provider_name, provider_skill_dir in get_provider_skill_paths(skill).items():
        providers_meta[provider_name] = {
            "path": str(provider_skill_dir),
            "last_distributed_hash": provider_hashes[provider_name],
        }

    skills_meta[skill] = {
        "canonical_path": f"skills/{skill}",
        "tracked": True,
        "source": "kitty",
        "last_distributed_hash": canonical_hash,
        "providers": providers_meta,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_manifest(manifest)

    click.echo(f"Distribute completed: {skill}")
