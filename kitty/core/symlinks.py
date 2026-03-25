"""Symlink creation, validation, and management."""

from __future__ import annotations

import os
from enum import Enum, auto
from pathlib import Path

from .config import KITTY_HOME


def canonical_skill_path(skill: str) -> Path:
    return KITTY_HOME / "skills" / skill


class LinkState(Enum):
    CORRECT = auto()        # Symlink pointing to canonical path
    MISSING = auto()        # Path doesn't exist
    WRONG_SYMLINK = auto()  # Symlink but points elsewhere
    REAL_DIR = auto()       # Real directory or file (not a symlink)


def inspect_link(link_path: Path, skill: str) -> LinkState:
    canonical = canonical_skill_path(skill)
    if not link_path.exists() and not link_path.is_symlink():
        return LinkState.MISSING
    if link_path.is_symlink():
        target = Path(os.readlink(link_path))
        if target.resolve() == canonical.resolve():
            return LinkState.CORRECT
        return LinkState.WRONG_SYMLINK
    return LinkState.REAL_DIR


def create_symlink(link_path: Path, skill: str) -> None:
    """Create an absolute symlink at link_path → canonical skill path."""
    canonical = canonical_skill_path(skill)
    link_path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(str(canonical), str(link_path))


def remove_symlink(link_path: Path) -> None:
    """Remove a symlink (not the target)."""
    if link_path.is_symlink():
        link_path.unlink()
    else:
        raise ValueError(f"{link_path} is not a symlink")


def replace_symlink(link_path: Path, skill: str) -> None:
    """Remove existing symlink and recreate pointing to canonical."""
    if link_path.is_symlink():
        link_path.unlink()
    create_symlink(link_path, skill)
