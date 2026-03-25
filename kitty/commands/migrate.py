"""kitty migrate <skill> [--from <provider>]"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

import click

from ..core.config import KITTY_HOME, find_workspace_root
from ..core.git import add_and_commit, is_initialized
from ..core.symlinks import LinkState, canonical_skill_path, create_symlink, inspect_link
from ..core.providers import get_provider_paths, skill_link_paths


def _dir_hash(path: Path) -> str:
    """Compute a deterministic hash of all file contents in a directory."""
    h = hashlib.sha256()
    for fp in sorted(path.rglob("*")):
        if fp.is_file():
            h.update(str(fp.relative_to(path)).encode())
            h.update(fp.read_bytes())
    return h.hexdigest()


@click.command("migrate")
@click.argument("skill")
@click.option("--from", "from_provider", default=None, help="Which provider's directory to use as source.")
def cmd_migrate(skill: str, from_provider: str | None) -> None:
    """Migrate an existing real skill directory into the global store."""
    if not is_initialized():
        click.echo("Global store not found. Run `kitty init --global` first.", err=True)
        raise SystemExit(1)

    canonical = canonical_skill_path(skill)
    if canonical.exists():
        click.echo(
            f"Skill '{skill}' already exists in global store.\n"
            "Use `kitty checkout {skill}` to pull the remote version, or resolve manually.",
            err=True,
        )
        raise SystemExit(1)

    workspace = find_workspace_root()
    provider_paths = get_provider_paths(workspace)

    # Find real directories for this skill
    real_dirs: dict[str, Path] = {}
    for name, skills_dir in provider_paths.items():
        candidate = skills_dir / skill
        state = inspect_link(candidate, skill)
        if state == LinkState.REAL_DIR:
            real_dirs[name] = candidate

    if not real_dirs:
        click.echo(f"No real directory found for '{skill}' in any provider.", err=True)
        raise SystemExit(1)

    # Determine source
    if from_provider:
        if from_provider not in real_dirs:
            click.echo(
                f"Provider '{from_provider}' has no real directory for '{skill}'. "
                f"Found: {list(real_dirs)}",
                err=True,
            )
            raise SystemExit(1)
        source_name = from_provider
        source = real_dirs[from_provider]
    elif len(real_dirs) == 1:
        source_name, source = next(iter(real_dirs.items()))
    else:
        # Multiple real dirs — check if content is identical
        hashes = {name: _dir_hash(path) for name, path in real_dirs.items()}
        unique = set(hashes.values())
        if len(unique) == 1:
            # Same content everywhere — pick any
            source_name, source = next(iter(real_dirs.items()))
        else:
            click.echo(
                f"Multiple conflicting real directories found for '{skill}':\n"
                + "\n".join(f"  {n}: {p}" for n, p in real_dirs.items())
                + "\nSpecify --from <provider> to choose which version to keep.",
                err=True,
            )
            raise SystemExit(1)

    project_name = workspace.name

    # Copy to a temp location first (atomic)
    tmp = Path(tempfile.mkdtemp())
    tmp_skill = tmp / skill
    try:
        shutil.copytree(str(source), str(tmp_skill))
        # Move into canonical location
        shutil.copytree(str(tmp_skill), str(canonical))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    add_and_commit(
        [f"skills/{skill}"],
        f"kitty: migrate '{skill}' from {source_name}@{project_name}",
    )
    click.echo(f"Migrated '{skill}' to global store from {source_name}@{project_name}")

    # Replace source with symlink
    shutil.rmtree(str(source))
    create_symlink(source, skill)
    click.echo(f"  {source_name}: replaced with symlink ✓")

    # Handle other providers
    pairs = skill_link_paths(workspace, skill)
    for name, link_path in pairs:
        if str(link_path) == str(source):
            continue  # already done
        state = inspect_link(link_path, skill)
        if state == LinkState.MISSING:
            link_path.parent.mkdir(parents=True, exist_ok=True)
            create_symlink(link_path, skill)
            click.echo(f"  {name}: linked ✓")
        elif state == LinkState.REAL_DIR:
            other_hash = _dir_hash(link_path)
            canonical_h = _dir_hash(canonical)
            if other_hash == canonical_h:
                shutil.rmtree(str(link_path))
                create_symlink(link_path, skill)
                click.echo(f"  {name}: same content, replaced with symlink ✓")
            else:
                click.echo(
                    f"  {name}: conflicting content at {link_path}. "
                    f"Run `kitty migrate {skill} --from {name}` after resolving manually.",
                    err=True,
                )
        elif state == LinkState.CORRECT:
            click.echo(f"  {name}: already linked ✓")
