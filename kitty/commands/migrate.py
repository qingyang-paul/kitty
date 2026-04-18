"""kitty migrate path/to/skill_dir"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import click

from ..core.config import ensure_global_workspace, get_skills_dir, load_manifest, save_manifest


@click.command("migrate")
@click.argument(
    "skill_dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True),
)
def cmd_migrate(skill_dir: Path) -> None:
    """Import an existing skill directory into ~/.kitty/skills."""
    ensure_global_workspace()

    source_dir = skill_dir.resolve()
    skill_name = source_dir.name
    target_dir = (get_skills_dir() / skill_name).resolve()

    if source_dir == target_dir:
        click.echo(f"Warning: '{skill_name}' is already managed by kitty: {target_dir}", err=True)
        return

    if target_dir.exists():
        click.echo(
            f"Warning: skill '{skill_name}' already exists in kitty at {target_dir}. "
            "Skipped to avoid overwrite.",
            err=True,
        )
        return

    shutil.copytree(source_dir, target_dir)

    manifest = load_manifest()
    skills_meta = manifest.setdefault("skills", {})
    skills_meta[skill_name] = {
        "canonical_path": f"skills/{skill_name}",
        "tracked": True,
        "source": "migrate",
        "migrated_from": str(source_dir),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_manifest(manifest)

    click.echo(f"Migrated '{skill_name}' from {source_dir}")
    click.echo(f"Canonical path: {target_dir}")
