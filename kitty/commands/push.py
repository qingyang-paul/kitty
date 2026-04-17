"""kitty push [<skill>] [--force]"""

from __future__ import annotations

from pathlib import Path

import click

from ..core.config import KITTY_HOME, find_workspace_root, has_remote
from ..core.params import SKILL
from ..core.git import (
    add_and_commit,
    diff_remote,
    fetch as git_fetch,
    git,
    is_initialized,
    push as git_push,
    status_porcelain,
)
from datetime import datetime, timezone


def _build_commit_message(skill: str, workspace: Path, dirty_files: list[str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project = workspace.name
    files_summary = "\n".join(f"  - {f}" for f in dirty_files[:10])
    if len(dirty_files) > 10:
        files_summary += f"\n  - (+{len(dirty_files) - 10} more)"
    return f"kitty: update '{skill}' [{project}] {ts}\n\nSkills modified:\n{files_summary}"


@click.command("push")
@click.argument("skill", required=False, default=None, type=SKILL)
@click.option("--force", is_flag=True, help="Force push to remote (uses --force-with-lease).")
def cmd_push(skill: str | None, force: bool) -> None:
    """Commit changes and push to remote.

    \b
    Usage:
      kitty push               Commit and push all modified skills
      kitty push <skill>       Commit and push a specific skill
      kitty push <skill> --force   Force push (uses --force-with-lease)
    \b
    Examples:
      kitty push
      kitty push code-review
      kitty push code-review --force
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    workspace = find_workspace_root()
    skills_dir = KITTY_HOME / "skills"

    # Determine which skills to push
    if skill:
        skills = [skill]
    else:
        skills = [d.name for d in skills_dir.iterdir() if d.is_dir()] if skills_dir.exists() else []

    any_pushed = False
    for s in skills:
        dirty = status_porcelain(path=f"skills/{s}")
        if not dirty:
            if skill:  # Only show "nothing" if explicitly requested
                click.echo(f"'{s}': nothing to push (working tree clean).")
            continue

        dirty_files = [fp.replace(f"skills/{s}/", "") for _, fp in dirty]
        msg = _build_commit_message(s, workspace, dirty_files)
        add_and_commit([f"skills/{s}"], msg)
        click.echo(f"Committed '{s}' ({len(dirty_files)} file(s) changed).")
        any_pushed = True

    if not any_pushed and not skill:
        click.echo("Nothing to push. All skills are clean.")
        return

    # Push to remote
    if not has_remote():
        click.echo("Committed locally. No remote configured — changes are local only.")
        click.echo("Set 'remote' in ~/.kitty/config.json to enable multi-machine sync.")
        return

    result = git_push(force=force)
    if result.returncode == 0:
        click.echo("Pushed to origin/main ✓")
        return

    # Push rejected — divergent history
    stderr = result.stderr
    if "rejected" in stderr or "non-fast-forward" in stderr:
        click.echo("\nPush rejected: remote has divergent changes.", err=True)
        click.echo("Fetching remote to show diff...")
        git_fetch()
        if skill:
            diff = diff_remote(f"skills/{skill}")
            if diff:
                click.echo("\n--- Diff (remote vs local) ---")
                click.echo(diff[:2000])
                if len(diff) > 2000:
                    click.echo("... (truncated)")
        click.echo(
            "\nOptions:\n"
            f"  kitty push --force {skill or '<skill>'}   Overwrite remote with your version\n"
            f"  kitty checkout {skill or '<skill>'}       Discard local, use remote version",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Push failed:\n{stderr}", err=True)
    raise SystemExit(1)
