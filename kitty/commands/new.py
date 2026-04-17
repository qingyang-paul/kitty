"""kitty new <skill>"""

from __future__ import annotations

import re

import click

from ..core.config import DEFAULT_SKILL_MD, KITTY_HOME, find_workspace_root
from ..core.git import add_and_commit, is_initialized
from ..core.symlinks import canonical_skill_path, create_symlink, inspect_link, LinkState
from ..core.providers import skill_link_paths

SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]*$")


def validate_skill_name(name: str) -> None:
    if not SKILL_NAME_RE.match(name):
        raise click.BadParameter(
            f"'{name}' is invalid. Use lowercase letters, digits, hyphens, underscores only."
        )


@click.command("new")
@click.argument("skill")
def cmd_new(skill: str) -> None:
    """Create a new skill in the global store and link it to workspace providers.

    \b
    Usage:
      kitty new <skill>        Scaffold skill in ~/.kitty/skills/<skill>/ and link it here
    \b
    Examples:
      kitty new code-review
      kitty new data-analysis
    """
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    validate_skill_name(skill)

    canonical = canonical_skill_path(skill)
    if canonical.exists():
        click.echo(f"Skill '{skill}' already exists. Use `kitty link {skill}` to link it.")
        raise SystemExit(1)

    # Create skill directory + scaffold
    canonical.mkdir(parents=True)
    (canonical / "SKILL.md").write_text(DEFAULT_SKILL_MD.format(skill=skill))

    add_and_commit([f"skills/{skill}"], f"kitty: create skill '{skill}'")
    click.echo(f"Created skill '{skill}'")

    # Link into workspace providers
    workspace = find_workspace_root()
    _link_skill(skill, workspace)


def _link_skill(skill: str, workspace, provider: str | None = None, force: bool = False) -> None:
    """Internal: create symlinks for a skill in workspace providers."""
    pairs = skill_link_paths(workspace, skill, provider)
    linked = []
    for name, link_path in pairs:
        state = inspect_link(link_path, skill)
        if state == LinkState.CORRECT:
            click.echo(f"  {name}: already linked")
        elif state == LinkState.MISSING:
            link_path.parent.mkdir(parents=True, exist_ok=True)
            create_symlink(link_path, skill)
            linked.append(name)
        elif state == LinkState.WRONG_SYMLINK:
            if force:
                from ..core.symlinks import replace_symlink
                replace_symlink(link_path, skill)
                linked.append(name)
            else:
                click.echo(
                    f"  {name}: symlink exists but points elsewhere. Use --force to relink.",
                    err=True,
                )
        elif state == LinkState.REAL_DIR:
            click.echo(
                f"  {name}: real directory found at {link_path}. "
                f"Run `kitty migrate {skill}` to migrate it.",
                err=True,
            )

    if linked:
        click.echo(f"  Linked [{', '.join(linked)}]")
