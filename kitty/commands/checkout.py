"""kitty checkout <skill>"""

from __future__ import annotations

import click

from ..core.config import KITTY_HOME
from ..core.params import SKILL
from ..core.git import (
    add_and_commit,
    checkout_from_remote,
    is_initialized,
    log_ahead,
    status_porcelain,
)


def _auto_snapshot(skill: str) -> bool:
    """Hook: if there are uncommitted local changes, commit them before overwrite."""
    dirty = [fp for code, fp in status_porcelain(path=f"skills/{skill}")]
    if dirty:
        click.echo(f"  Auto-snapshot: committing {len(dirty)} uncommitted file(s) before overwrite...")
        add_and_commit(
            [f"skills/{skill}"],
            f"kitty: auto-snapshot '{skill}' before checkout",
        )
        return True
    return False


@click.command("checkout")
@click.argument("skill", type=SKILL)
def cmd_checkout(skill: str) -> None:
    """Overwrite local skill with the latest remote version (destructive).

    Uncommitted local changes are auto-snapshotted to a branch before overwriting.

    \b
    Usage:
      kitty checkout <skill>   Pull remote version and overwrite local copy
    \b
    Examples:
      kitty checkout code-review
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    canonical = KITTY_HOME / "skills" / skill
    if not canonical.exists():
        click.echo(
            f"Skill '{skill}' not in local store. Run `kitty clone {skill}` first.",
            err=True,
        )
        raise SystemExit(1)

    ahead = log_ahead(path=f"skills/{skill}")
    if not ahead:
        click.echo(f"'{skill}' is already up to date.")
        return

    # Hook: auto-snapshot before destructive overwrite
    _auto_snapshot(skill)

    checkout_from_remote(f"skills/{skill}")
    add_and_commit(
        [f"skills/{skill}"],
        f"kitty: checkout '{skill}' from remote",
    )

    click.echo(f"Updated '{skill}' ({len(ahead)} commit(s) applied).")
    click.echo("All provider symlinks updated automatically.")
