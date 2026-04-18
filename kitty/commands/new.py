"""kitty new <skill>"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import click

from ..core.config import DEFAULT_SKILL_MD, ensure_global_workspace, get_skills_dir, load_manifest, save_manifest

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_skill_name(name: str) -> None:
    if not SKILL_NAME_RE.match(name):
        raise click.BadParameter(
            f"'{name}' is invalid. Use lowercase letters, digits, hyphens only."
        )


@click.command("new")
@click.argument("skill")
@click.option(
    "-f",
    "source_markdown",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, file_okay=True),
    required=False,
    help="Use this markdown file as SKILL.md content.",
)
def cmd_new(skill: str, source_markdown: Path | None) -> None:
    """Create a new skill under ~/.kitty/skills."""
    ensure_global_workspace()
    validate_skill_name(skill)

    skill_dir = get_skills_dir() / skill
    if skill_dir.exists():
        click.echo(f"Skill '{skill}' already exists.", err=True)
        raise SystemExit(1)

    skill_dir.mkdir(parents=True, exist_ok=False)
    skill_md_path = skill_dir / "SKILL.md"
    if source_markdown is None:
        skill_md_path.write_text(DEFAULT_SKILL_MD.format(skill=skill))
    else:
        skill_md_path.write_text(source_markdown.read_text())

    manifest = load_manifest()
    skills_meta = manifest.setdefault("skills", {})
    skills_meta[skill] = {
        "canonical_path": f"skills/{skill}",
        "tracked": True,
        "source": "new",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_manifest(manifest)

    click.echo(f"Created skill '{skill}' at {skill_dir}")
    click.echo(f"Edit with: kitty edit {skill}")
