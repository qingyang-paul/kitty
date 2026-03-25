"""Kitty CLI entry point."""

import click

from .commands.init import cmd_init
from .commands.new import cmd_new
from .commands.link import cmd_link
from .commands.unlink import cmd_unlink
from .commands.migrate import cmd_migrate
from .commands.status import cmd_status
from .commands.list_ import cmd_list
from .commands.fetch import cmd_fetch
from .commands.checkout import cmd_checkout
from .commands.push import cmd_push
from .commands.clone import cmd_clone


@click.group()
def main() -> None:
    """Kitty — skill manager for AI agents (Claude, Gemini, Codex)."""


main.add_command(cmd_init)
main.add_command(cmd_new)
main.add_command(cmd_link)
main.add_command(cmd_unlink)
main.add_command(cmd_migrate)
main.add_command(cmd_status)
main.add_command(cmd_list)
main.add_command(cmd_fetch)
main.add_command(cmd_checkout)
main.add_command(cmd_push)
main.add_command(cmd_clone)
