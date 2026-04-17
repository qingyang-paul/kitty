"""kitty unlink <skill> [--provider X]"""

from __future__ import annotations

import click

from ..core.config import find_workspace_root
from ..core.git import is_initialized
from ..core.symlinks import LinkState, inspect_link, remove_symlink
from ..core.providers import skill_link_paths


@click.command("unlink")
@click.argument("skill")
@click.option("--provider", "-p", default=None, help="Only unlink from this provider.")
def cmd_unlink(skill: str, provider: str | None) -> None:
    """Remove symlinks for a skill from workspace provider directories.

    \b
    Usage:
      kitty unlink <skill>              Remove symlinks from all providers
      kitty unlink <skill> -p <provider>  Remove symlink from one provider only
    \b
    Examples:
      kitty unlink code-review
      kitty unlink code-review -p claude
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    workspace = find_workspace_root()

    try:
        pairs = skill_link_paths(workspace, skill, provider)
    except ValueError as e:
        click.echo(f"error: {e}", err=True)
        raise SystemExit(1)

    for name, link_path in pairs:
        state = inspect_link(link_path, skill)
        if state == LinkState.MISSING:
            click.echo(f"  {name}: not linked (nothing to do)")
        elif state in (LinkState.CORRECT, LinkState.WRONG_SYMLINK):
            remove_symlink(link_path)
            click.echo(f"  {name}: unlinked {link_path}")
        elif state == LinkState.REAL_DIR:
            click.echo(
                f"  {name}: real directory at {link_path}, not a symlink. "
                "Run `kitty migrate` if you want to manage it.",
                err=True,
            )
