"""kitty clone <skill>"""

from __future__ import annotations

import click

from ..core.config import KITTY_HOME, find_workspace_root, has_remote
from ..core.git import (
    add_and_commit,
    checkout_from_remote,
    fetch as git_fetch,
    is_initialized,
    ls_tree_remote,
)
from .link import _do_link


@click.command("clone")
@click.argument("skill")
def cmd_clone(skill: str) -> None:
    """First-time: fetch a skill from remote and link it to all workspace providers."""
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    canonical = KITTY_HOME / "skills" / skill
    if canonical.exists():
        click.echo(
            f"Skill '{skill}' already in local store.\n"
            f"  Use `kitty link {skill}` to link it to this workspace.\n"
            f"  Use `kitty checkout {skill}` to update it from remote."
        )
        return

    if not has_remote():
        click.echo(
            f"No remote configured and '{skill}' is not in local store.\n"
            "Use `kitty new {skill}` to create it, or configure a remote in ~/.kitty/config.json.",
            err=True,
        )
        raise SystemExit(1)

    click.echo("Fetching from origin...")
    result = git_fetch()
    if result.returncode != 0:
        click.echo(f"Fetch failed:\n{result.stderr}", err=True)
        raise SystemExit(1)

    if not ls_tree_remote(f"skills/{skill}"):
        click.echo(f"Skill '{skill}' not found on remote.", err=True)
        raise SystemExit(1)

    checkout_from_remote(f"skills/{skill}")
    add_and_commit(
        [f"skills/{skill}"],
        f"kitty: clone '{skill}' from remote",
    )
    click.echo(f"Cloned '{skill}' from remote.")

    workspace = find_workspace_root()
    click.echo("Linking to providers:")
    _do_link(skill, workspace)
