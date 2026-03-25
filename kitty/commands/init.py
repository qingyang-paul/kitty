"""kitty init [--global]"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import click

from ..core.config import (
    DEFAULT_GLOBAL_CONFIG,  # used as the initial file template
    DEFAULT_KITTYIGNORE,
    KITTY_HOME,
    find_workspace_root,
    load_global_config,
    save_workspace_config,
)
from ..core.git import add_and_commit, init_repo, is_initialized
from ..core.providers import get_provider_paths


@click.command("init")
@click.option("--global", "global_", is_flag=True, help="Initialize the global ~/.kitty/ store.")
def cmd_init(global_: bool) -> None:
    """Initialize Kitty environment (global store or workspace)."""
    if global_:
        _init_global()
    else:
        _init_workspace()


def _init_global() -> None:
    if is_initialized():
        click.echo(f"~/.kitty already initialized at {KITTY_HOME}")
        return

    KITTY_HOME.mkdir(parents=True, exist_ok=True)
    (KITTY_HOME / "skills").mkdir(exist_ok=True)

    # Write config.json (only if absent — user may have pre-staged a custom one)
    cfg_path = KITTY_HOME / "config.json"
    if not cfg_path.exists():
        with open(cfg_path, "w") as f:
            json.dump(DEFAULT_GLOBAL_CONFIG, f, indent=2)
            f.write("\n")

    # Write .kittyignore
    kittyignore = KITTY_HOME / ".kittyignore"
    if not kittyignore.exists():
        kittyignore.write_text(DEFAULT_KITTYIGNORE)

    # Read back from file so user-customised commit_author is respected
    cfg = load_global_config()
    author = cfg.get("commit_author", DEFAULT_GLOBAL_CONFIG["commit_author"])

    # Git init + configure
    init_repo(
        author_name=author["name"],
        author_email=author["email"],
    )

    add_and_commit(
        ["config.json", ".kittyignore"],
        "kitty: initialize global store",
    )

    click.echo(f"Initialized kitty global store at {KITTY_HOME}")
    click.echo("Next: kitty init  (in your workspace)")


def _init_workspace() -> None:
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    workspace = find_workspace_root()
    kitty_dir = workspace / ".kitty"
    ws_cfg_path = kitty_dir / "config.json"

    # Create .kitty/ dir
    kitty_dir.mkdir(exist_ok=True)

    # Write workspace config if absent
    if not ws_cfg_path.exists():
        global_cfg = load_global_config()
        ws_cfg = {"version": 1, "providers": global_cfg.get("default_providers", ["claude", "gemini"])}
        save_workspace_config(workspace, ws_cfg)
        click.echo(f"Created .kitty/config.json")

    # Copy .kittyignore if absent
    ws_kittyignore = workspace / ".kittyignore"
    if not ws_kittyignore.exists():
        shutil.copy(KITTY_HOME / ".kittyignore", ws_kittyignore)
        click.echo("Created .kittyignore (copied from global)")

    # Create provider skills directories (deduplicated)
    provider_paths = get_provider_paths(workspace)
    created_dirs: set[str] = set()
    for name, skills_dir in provider_paths.items():
        key = str(skills_dir)
        if key not in created_dirs:
            skills_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.add(key)

    click.echo(f"Workspace initialized at {workspace}")
    click.echo("Run `kitty new <skill>` to create a skill or `kitty link` to link existing ones.")
