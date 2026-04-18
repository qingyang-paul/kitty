"""kitty init"""

from __future__ import annotations

import click

from ..core.config import ensure_global_workspace, get_kitty_home


@click.command("init")
def cmd_init() -> None:
    """Initialize (or repair) the global kitty workspace at ~/.kitty."""
    created = ensure_global_workspace()
    kitty_home = get_kitty_home()

    if not created:
        click.echo(f"Kitty already initialized at {kitty_home}")
        return

    click.echo(f"Kitty initialized at {kitty_home}")
    click.echo("Created:")
    for path in created:
        click.echo(f"  - {path}")
