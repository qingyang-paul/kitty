"""Custom Click parameter types with shell completion."""

from __future__ import annotations

import click
from click.shell_completion import CompletionItem

from .config import KITTY_HOME, load_global_config


class SkillParam(click.ParamType):
    """Skill name with tab-completion from ~/.kitty/skills/."""

    name = "skill"

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        skills_dir = KITTY_HOME / "skills"
        if not skills_dir.exists():
            return []
        return [
            CompletionItem(d.name)
            for d in sorted(skills_dir.iterdir())
            if d.is_dir() and d.name.startswith(incomplete)
        ]


class ProviderParam(click.ParamType):
    """Provider name with tab-completion from global config."""

    name = "provider"

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        cfg = load_global_config()
        providers = cfg.get("providers", {}).keys()
        return [
            CompletionItem(name)
            for name in sorted(providers)
            if name.startswith(incomplete)
        ]


SKILL = SkillParam()
PROVIDER = ProviderParam()
