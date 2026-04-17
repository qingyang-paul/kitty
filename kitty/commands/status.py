"""kitty status [<skill>]"""

from __future__ import annotations

from pathlib import Path

import click

from ..core.config import KITTY_HOME, find_workspace_root, has_remote
from ..core.git import (
    is_initialized,
    log_ahead,
    log_unpushed,
    status_porcelain,
    fetch as git_fetch,
)
from ..core.symlinks import LinkState, inspect_link
from ..core.providers import get_provider_paths
from ..core.params import SKILL


@click.command("status")
@click.argument("skill", required=False, default=None, type=SKILL)
def cmd_status(skill: str | None) -> None:
    """Show consistency status: uncommitted changes, symlink health, remote delta.

    \b
    Usage:
      kitty status             Show status for all skills
      kitty status <skill>     Show status for a specific skill
    \b
    Examples:
      kitty status
      kitty status code-review
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    skills_dir = KITTY_HOME / "skills"
    if not skills_dir.exists():
        click.echo("No skills yet.")
        return

    skills = [skill] if skill else sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
    workspace = find_workspace_root()
    provider_paths = get_provider_paths(workspace)

    # --- Section 1: Global store dirty state ---
    click.echo("~/.kitty global store:")
    dirty = {fp: code for code, fp in status_porcelain()}
    for s in skills:
        skill_prefix = f"skills/{s}/"
        modified_files = [fp.replace(skill_prefix, "") for fp, code in dirty.items() if fp.startswith(skill_prefix)]
        if modified_files:
            files_str = ", ".join(modified_files[:3])
            if len(modified_files) > 3:
                files_str += f" (+{len(modified_files) - 3} more)"
            click.echo(f"  {s:<30} modified ({files_str})")
        else:
            click.echo(f"  {s:<30} clean")

    # --- Section 2: Symlink health ---
    click.echo("\nWorkspace symlinks:")
    provider_labels = "/".join(f"{p}" for p in provider_paths)
    click.echo(f"  ({provider_labels})")

    for s in skills:
        states: dict[str, str] = {}
        seen_paths: set[str] = set()
        for name, skills_dir_p in provider_paths.items():
            link_path = skills_dir_p / s
            key = str(link_path)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            state = inspect_link(link_path, s)
            if state == LinkState.CORRECT:
                states[name] = "✓"
            elif state == LinkState.MISSING:
                states[name] = "missing"
            elif state == LinkState.WRONG_SYMLINK:
                states[name] = "wrong target"
            elif state == LinkState.REAL_DIR:
                states[name] = "real dir (not linked)"

        state_str = "  ".join(f"{n}:{v}" for n, v in states.items())
        click.echo(f"  {s:<30} {state_str}")

    # --- Section 3: Remote delta ---
    if has_remote():
        click.echo("\nRemote (origin/main):")
        for s in skills:
            ahead = log_ahead(path=f"skills/{s}")
            unpushed = log_unpushed(path=f"skills/{s}")
            if ahead:
                click.echo(f"  {s:<30} remote {len(ahead)} commit(s) ahead → run `kitty checkout {s}`")
            elif unpushed:
                click.echo(f"  {s:<30} {len(unpushed)} unpushed commit(s) → run `kitty push {s}`")
            else:
                click.echo(f"  {s:<30} up to date")
    else:
        click.echo("\nRemote: not configured (single-machine mode)")
