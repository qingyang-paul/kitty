"""kitty link [<skill>] [--provider X] [--force]"""

from __future__ import annotations

from pathlib import Path

import click

from ..core.config import KITTY_HOME, find_workspace_root
from ..core.git import is_initialized
from ..core.symlinks import LinkState, canonical_skill_path, create_symlink, inspect_link, replace_symlink
from ..core.providers import skill_link_paths


@click.command("link")
@click.argument("skill", required=False, default=None)
@click.option("--provider", "-p", default=None, help="Only link for this provider.")
@click.option("--force", is_flag=True, help="Overwrite wrong-target symlinks.")
def cmd_link(skill: str | None, provider: str | None, force: bool) -> None:
    """Create symlinks for skill(s) in workspace provider directories.

    \b
    Usage:
      kitty link               Link all global-store skills to this workspace
      kitty link <skill>       Link a specific skill
      kitty link <skill> -p <provider>   Link only for one provider
      kitty link <skill> --force         Overwrite wrong-target symlinks
    \b
    Examples:
      kitty link
      kitty link code-review
      kitty link code-review -p codex
      kitty link code-review --force
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    workspace = find_workspace_root()
    skills_dir = KITTY_HOME / "skills"

    if skill:
        skills = [skill]
    else:
        if not skills_dir.exists():
            click.echo("No skills in global store yet.")
            return
        skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]

    if not skills:
        click.echo("No skills found.")
        return

    for s in skills:
        canonical = canonical_skill_path(s)
        if not canonical.exists():
            click.echo(f"Skill '{s}' not in global store. Run `kitty fetch {s}` or `kitty new {s}`.", err=True)
            continue

        click.echo(f"{s}:")
        _do_link(s, workspace, provider, force)


def _do_link(skill: str, workspace: Path, provider: str | None = None, force: bool = False) -> None:
    try:
        pairs = skill_link_paths(workspace, skill, provider)
    except ValueError as e:
        click.echo(f"  error: {e}", err=True)
        return

    for name, link_path in pairs:
        state = inspect_link(link_path, skill)
        if state == LinkState.CORRECT:
            click.echo(f"  {name}: already linked ✓")
        elif state == LinkState.MISSING:
            link_path.parent.mkdir(parents=True, exist_ok=True)
            create_symlink(link_path, skill)
            click.echo(f"  {name}: linked → {link_path}")
        elif state == LinkState.WRONG_SYMLINK:
            if force:
                replace_symlink(link_path, skill)
                click.echo(f"  {name}: relinked (--force)")
            else:
                import os
                target = os.readlink(str(link_path))
                click.echo(f"  {name}: symlink points to {target}. Use --force to relink.", err=True)
        elif state == LinkState.REAL_DIR:
            click.echo(
                f"  {name}: real directory at {link_path} — run `kitty migrate {skill}` first.",
                err=True,
            )
