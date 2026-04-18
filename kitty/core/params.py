"""Custom Click parameter types with shell completion."""

from __future__ import annotations

import click
from click.shell_completion import CompletionItem

from .config import get_kitty_home


def complete_skill_names(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
    skills_dir = get_kitty_home() / "skills"
    if not skills_dir.exists():
        return []
    return [
        CompletionItem(d.name)
        for d in sorted(skills_dir.iterdir())
        if d.is_dir() and d.name.startswith(incomplete)
    ]


class SkillParam(click.ParamType):
    """Skill name with tab-completion from ~/.kitty/skills/."""

    name = "skill"

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        return complete_skill_names(ctx, param, incomplete)


SKILL = SkillParam()
