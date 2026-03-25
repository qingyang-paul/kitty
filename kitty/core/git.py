"""Git subprocess wrappers for ~/.kitty/ operations."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from .config import KITTY_HOME, load_global_config


def _run(args: list[str], cwd: Path = KITTY_HOME, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run git in ~/.kitty/."""
    return _run(["git", *args], check=check)


def is_initialized() -> bool:
    return (KITTY_HOME / ".git").is_dir()


def init_repo(author_name: str = "kitty", author_email: str = "kitty@local") -> None:
    _run(["git", "init", str(KITTY_HOME)])
    git("config", "user.name", author_name)
    git("config", "user.email", author_email)
    # Use .kittyignore as the excludes file
    kittyignore = KITTY_HOME / ".kittyignore"
    git("config", "core.excludesFile", str(kittyignore))


def add_and_commit(paths: list[str], message: str) -> None:
    """Stage paths and create a commit."""
    git("add", "--", *paths)
    # Check if there's anything staged
    result = git("diff", "--cached", "--quiet", check=False)
    if result.returncode == 0:
        return  # Nothing staged
    git("commit", "-m", message)


def set_remote(url: str) -> None:
    result = git("remote", "get-url", "origin", check=False)
    if result.returncode == 0:
        git("remote", "set-url", "origin", url)
    else:
        git("remote", "add", "origin", url)


def fetch() -> subprocess.CompletedProcess:
    return git("fetch", "origin", check=False)


def push(force: bool = False) -> subprocess.CompletedProcess:
    args = ["push", "origin", "main"]
    if force:
        args.append("--force-with-lease")
    return git(*args, check=False)


def log_ahead(ref: str = "HEAD", remote_ref: str = "origin/main", path: Optional[str] = None) -> list[str]:
    """Return commit hashes in remote_ref but not in ref (i.e. remote is ahead)."""
    args = ["log", f"{ref}..{remote_ref}", "--oneline", "--format=%H %s"]
    if path:
        args += ["--", path]
    result = git(*args, check=False)
    if result.returncode != 0:
        return []
    return [l for l in result.stdout.strip().splitlines() if l]


def log_unpushed(path: Optional[str] = None) -> list[str]:
    """Return commits in HEAD but not in origin/main."""
    args = ["log", "origin/main..HEAD", "--oneline", "--format=%H %s"]
    if path:
        args += ["--", path]
    result = git(*args, check=False)
    if result.returncode != 0:
        return []
    return [l for l in result.stdout.strip().splitlines() if l]


def status_porcelain(path: Optional[str] = None) -> list[tuple[str, str]]:
    """Return list of (status_code, filepath) for dirty files."""
    args = ["status", "--porcelain"]
    if path:
        args.append(path)
    result = git(*args, check=False)
    if result.returncode != 0:
        return []
    entries = []
    for line in result.stdout.splitlines():
        if line.strip():
            code = line[:2].strip()
            fp = line[3:]
            entries.append((code, fp))
    return entries


def checkout_from_remote(skill_path: str) -> None:
    """Overwrite working tree path with origin/main version."""
    git("checkout", "origin/main", "--", skill_path)


def ls_tree_remote(path: str) -> bool:
    """Return True if path exists in origin/main."""
    result = git("ls-tree", "-d", "origin/main", path, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def diff_remote(path: str) -> str:
    """Show diff between HEAD and origin/main for a path."""
    result = git("diff", "HEAD", "origin/main", "--", path, check=False)
    return result.stdout


def reflog(n: int = 20) -> str:
    result = git("reflog", f"-{n}", check=False)
    return result.stdout


def show(ref: str, path: str) -> str:
    result = git("show", f"{ref}:{path}", check=False)
    return result.stdout
