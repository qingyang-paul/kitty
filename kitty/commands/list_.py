"""kitty list [local|remote]"""

from __future__ import annotations

import re
from pathlib import Path

import click

from ..core.config import KITTY_HOME, has_remote
from ..core.git import git, is_initialized, log_ahead


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
        m = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if m:
            result[m.group(1)] = m.group(2).strip().strip('"').strip("'").strip(">").strip()
    return result


@click.command("list")
@click.argument("region", required=False, default="local", type=click.Choice(["local", "remote"]))
def cmd_list(region: str) -> None:
    """List tracked skills (local or remote)."""
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    if region == "local":
        _list_local()
    else:
        _list_remote()


def _list_local() -> None:
    skills_dir = KITTY_HOME / "skills"
    if not skills_dir.exists() or not any(skills_dir.iterdir()):
        click.echo("No local skills yet. Run `kitty new <skill>` to create one.")
        return

    click.echo(f"{'SKILL':<30}  {'DESCRIPTION'}")
    click.echo("-" * 70)
    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir():
            continue
        fm = _read_frontmatter(d)
        desc = fm.get("description", "")[:55] or "(no description)"
        click.echo(f"{d.name:<30}  {desc}")


def _list_remote() -> None:
    if not has_remote():
        click.echo("No remote configured. Set 'remote' in ~/.kitty/config.json")
        return

    result = git("ls-tree", "--name-only", "origin/main", "skills/", check=False)
    if result.returncode != 0:
        click.echo("Could not read remote. Run `kitty fetch` first.")
        return

    local_skills = set()
    skills_dir = KITTY_HOME / "skills"
    if skills_dir.exists():
        local_skills = {d.name for d in skills_dir.iterdir() if d.is_dir()}

    remote_skills = [
        line.replace("skills/", "").strip("/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    if not remote_skills:
        click.echo("No skills on remote.")
        return

    click.echo(f"{'SKILL':<30}  {'LOCAL':<10}")
    click.echo("-" * 50)
    for s in sorted(remote_skills):
        local_status = "✓ local" if s in local_skills else "missing"
        click.echo(f"{s:<30}  {local_status}")
