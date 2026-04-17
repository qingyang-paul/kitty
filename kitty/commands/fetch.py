"""kitty fetch [<skill>]"""

from __future__ import annotations

import click

from ..core.config import KITTY_HOME, has_remote
from ..core.git import fetch as git_fetch, is_initialized, log_ahead


@click.command("fetch")
@click.argument("skill", required=False, default=None)
def cmd_fetch(skill: str | None) -> None:
    """Safely download remote updates without touching the working tree.

    \b
    Usage:
      kitty fetch              Fetch all remote updates
      kitty fetch <skill>      Fetch updates for a specific skill only
    \b
    Examples:
      kitty fetch
      kitty fetch code-review
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    if not has_remote():
        click.echo("No remote configured. Single-machine mode — nothing to fetch.")
        click.echo("Set 'remote' in ~/.kitty/config.json to enable multi-machine sync.")
        return

    click.echo("Fetching from origin...")
    result = git_fetch()
    if result.returncode != 0:
        click.echo(f"Fetch failed:\n{result.stderr}", err=True)
        raise SystemExit(1)

    # Report status per skill
    skills_dir = KITTY_HOME / "skills"
    if skill:
        skills = [skill]
    else:
        skills = sorted(d.name for d in skills_dir.iterdir() if d.is_dir()) if skills_dir.exists() else []

    if not skills:
        click.echo("No local skills to compare.")
        return

    click.echo(f"\n{'SKILL':<30}  STATUS")
    click.echo("-" * 55)
    for s in skills:
        ahead = log_ahead(path=f"skills/{s}")
        if ahead:
            click.echo(f"  {s:<28}  remote {len(ahead)} commit(s) ahead → `kitty checkout {s}`")
        else:
            click.echo(f"  {s:<28}  up to date")
