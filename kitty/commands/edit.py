"""kitty edit <skill> [typora|antigravity]"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

import click

from ..core.config import ensure_global_workspace, get_skills_dir, load_global_config
from ..core.params import complete_skill_names

EDITOR_APP_MAP = {
    "typora": "Typora",
    "antigravity": "Antigravity",
}


def _open_path(target_path: Path, editor: str | None) -> None:
    system = platform.system().lower()

    if system == "darwin":
        if editor:
            app_name = EDITOR_APP_MAP[editor]
            subprocess.run(["open", "-a", app_name, str(target_path)], check=True)
            return
        subprocess.run(["open", str(target_path)], check=True)
        return

    if system == "windows":
        if editor:
            subprocess.run([editor, str(target_path)], check=True)
            return
        os.startfile(str(target_path))  # type: ignore[attr-defined]
        return

    if editor:
        subprocess.run([editor, str(target_path)], check=True)
        return
    subprocess.run(["xdg-open", str(target_path)], check=True)


@click.command("edit")
@click.argument("skill", type=click.STRING, shell_complete=complete_skill_names)
@click.argument("editor", required=False, type=click.Choice(["typora", "antigravity"]))
def cmd_edit(skill: str, editor: str | None) -> None:
    """Open one skill directory under ~/.kitty/skills with your editor."""
    ensure_global_workspace()

    skill_dir = get_skills_dir() / skill
    if not skill_dir.exists():
        click.echo(f"Skill '{skill}' not found at {skill_dir}", err=True)
        raise SystemExit(1)

    selected_editor = editor
    if selected_editor is None:
        cfg = load_global_config()
        default_editor = cfg.get("default_editor")
        if default_editor in {"typora", "antigravity"}:
            selected_editor = default_editor

    try:
        _open_path(skill_dir, selected_editor)
    except FileNotFoundError:
        click.echo("Editor application not found. Install it or pass another editor.", err=True)
        raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        click.echo(f"Failed to open editor: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"Opened '{skill}' at {skill_dir}")
