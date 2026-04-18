"""kitty list"""

from __future__ import annotations

import re
from pathlib import Path

import click

from ..core.config import ensure_global_workspace, get_skills_dir


def _read_frontmatter(skill_path: Path) -> dict[str, str]:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {}
    text = skill_md.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    frontmatter = text[3:end]
    result: dict[str, str] = {}
    for line in frontmatter.splitlines():
        matched = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if matched:
            result[matched.group(1)] = matched.group(2).strip().strip('"').strip("'").strip(">").strip()
    return result


@click.command("list")
def cmd_list() -> None:
    """List all skills under ~/.kitty/skills."""
    ensure_global_workspace()
    skills_dir = get_skills_dir()
    if not skills_dir.exists() or not any(skills_dir.iterdir()):
        click.echo("No skills yet. Run `kitty new <skill>`.")
        return

    click.echo(f"{'SKILL':<30}  DESCRIPTION")
    click.echo("-" * 70)
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        metadata = _read_frontmatter(skill_dir)
        desc = metadata.get("description", "")[:55] or "(no description)"
        click.echo(f"{skill_dir.name:<30}  {desc}")
