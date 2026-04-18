# Kitty

Copy-based AI skill manager with one canonical source.

Kitty keeps all canonical skills in `~/.kitty/skills/`, then distributes **copies** to:

- `~/.claude/skills/`
- `~/.agents/skills/`
- `~/.codex/skills/`

This version does not use symlinks and does not depend on per-project workspaces.

## Core Model

1. Single source of truth: `~/.kitty/skills/<skill>/`
2. Distribute by copy: `kitty distribute <skill>`
3. Track consistency via `kitty status`

## Installation

Prerequisites:

- Python 3.9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

Install from source:

```bash
uv tool install .
```

If needed, ensure `~/.local/bin` is in `PATH`.

## Commands

```bash
kitty init
kitty new <skill> [-f path/to/xx.md]
kitty migrate path/to/skill_dir
kitty edit <skill> [typora|antigravity]
kitty distribute <skill>
kitty status
kitty list
```

### `kitty init`

- Idempotent global initialization.
- Ensures `~/.kitty` exists and contains required files:
  - `.kittyignore`
  - `config.json`
  - `manifest.yaml`
  - `skills/`
- Also ensures provider directories exist under home.

### `kitty new <skill>`

- Creates `~/.kitty/skills/<skill>/SKILL.md`
- Optional: `-f path/to/xx.md` to use the file content as `SKILL.md`
- Updates `manifest.yaml`
- Skill name rule: lowercase letters, digits, and `-` only.

### `kitty migrate path/to/skill_dir`

- Imports an existing skill directory into `~/.kitty/skills/`
- Uses source directory name as skill name
- If a skill with the same name already exists in kitty, it prints a warning and skips overwrite

### `kitty edit <skill> [typora|antigravity]`

- Opens `~/.kitty/skills/<skill>` in your editor.
- If editor arg is omitted, uses `default_editor` from `config.json`.

### `kitty distribute <skill>`

- Copies canonical skill folder from `~/.kitty/skills/<skill>` to all providers.
- No provider selection flag in this version.
- Updates distribution hashes in `manifest.yaml`.

### `kitty status`

Shows:

- `SYNCED`: whether the skill is currently synced across all providers
- `PENDING_SYNC`: whether canonical content changed since last distribute
  - `yes`: modified but not distributed
  - `no`: no undistributed canonical change
- `LAST_MODIFIED`: latest local modification time under canonical skill directory
- Per-provider state:
  - `synced`
  - `changed`
  - `missing`
  - `invalid`

## Default Layout

```text
~/.kitty/
├── .kittyignore
├── config.json
├── manifest.yaml
└── skills/
    └── <skill>/
        └── SKILL.md

~/.claude/skills/
~/.agents/skills/
~/.codex/skills/
```

## Notes

- `manifest.yaml` is used as the skill index/state file.
- To override workspace path for testing/migration, you can still use:
  - `--workspace <path>`
  - `KITTY_WORKSPACE=<path>`
