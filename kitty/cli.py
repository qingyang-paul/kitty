"""Kitty CLI entry point."""

from pathlib import Path

import click

from .commands.distribute import cmd_distribute
from .commands.edit import cmd_edit
from .commands.init import cmd_init
from .commands.list_ import cmd_list
from .commands.migrate import cmd_migrate
from .commands.new import cmd_new
from .commands.status import cmd_status
from .core.config import get_kitty_home, set_kitty_home


@click.group()
@click.option(
    "--workspace",
    type=click.Path(path_type=Path, file_okay=False),
    envvar="KITTY_WORKSPACE",
    default=None,
    help="Kitty global workspace path. Priority: --workspace > KITTY_WORKSPACE > ~/.kitty",
)
@click.pass_context
def main(ctx: click.Context, workspace: Path | None) -> None:
    """Kitty — skill manager for AI agents (Claude, Gemini, Codex)."""
    set_kitty_home(workspace)
    ctx.ensure_object(dict)
    ctx.obj["kitty_home"] = str(get_kitty_home())


main.add_command(cmd_init)
main.add_command(cmd_new)
main.add_command(cmd_migrate)
main.add_command(cmd_edit)
main.add_command(cmd_distribute)
main.add_command(cmd_list)
main.add_command(cmd_status)
