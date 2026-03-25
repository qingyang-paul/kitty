# Kitty

**Cross-Agent, Cross-Workspace AI Skill Version Manager**

---

## Background

In modern AI development, the same set of skills often needs to serve multiple Agents simultaneously:

| Agent | Skills Path |
|---|---|
| Claude | `.claude/skills/` |
| Gemini / Codex | `.agents/skills/` |

This creates a persistent problem: you update and optimize a skill in one project, but another project's Claude is still using the old version; Gemini and Claude each have their own copy, and the content starts to drift; when moving to a new machine, you have to manually reconfigure all skills.

Kitty solves this.

---

## Design Concept

**Single Copy + Symlink + Git**

```
~/.kitty/skills/data-analysis/   ← Single source of truth (managed by git)
        │
        ├──→ ~/example_project/.claude/skills/data-analysis   (symlink)
        └──→ ~/example_project/.agents/skills/data-analysis   (symlink)
```

- `~/.kitty/` is a standard git repository where all skills are stored.
- Each provider directory contains symlinks, not file copies.
- Modify any location, and all providers see the update immediately—no manual synchronization needed.
- Provider paths defaults to **workspace relative paths** (`.claude/skills`). Just run commands in your project directory.

`kitty sync` does not exist: the symlink architecture makes the "who syncs with whom" problem disappear at the structural level.

---

## Installation

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Recommended) or pip

### Install with uv (Recommended)

Install directly from GitHub:

```bash
uv tool install git+https://github.com/qingyang-paul/kitty.git
```

Or clone and install locally:

```bash
git clone https://github.com/qingyang-paul/kitty.git ~/kitty
cd ~/kitty
uv tool install .
```

### Add to PATH

`uv tool install` places executables in `~/.local/bin/`. If the `kitty` command is not found, add this line to your shell configuration:

```bash
# ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

Then reload:

```bash
source ~/.zshrc   # or source ~/.bashrc
```

Verify installation:

```bash
kitty --help
```

> **Note**: macOS comes with a terminal emulator also named `kitty`. If a conflict occurs, place `~/.local/bin` at the front of your PATH (as shown above), or rename the entry point of this tool to `sk` (by modifying `[project.scripts]` in `pyproject.toml`).

---

### Updating the Tool

#### Installed via GitHub

Simply run:
```bash
uv tool upgrade kitty
```

#### Installed from Local Source

Navigate to the cloned directory and run the install command:

```bash
# Enter directory and pull latest code
cd ~/kitty
git pull

# Reinstall (--force to overwrite existing version)
uv tool install . --force
```

Single line command:

```bash
cd ~/kitty && git pull && uv tool install . --force
```

---

## Quick Start

### Step 1: Initialize Global Store (Once per machine)

```bash
kitty init --global
```

Creates `~/.kitty/` (git repo), default `config.json`, and `.kittyignore`.

### Step 2: Initialize Workspace in Project

```bash
cd ~/example_project
kitty init
```

Creates `.kitty/config.json` and prepares skill directories for Claude and Gemini in the project folder.

### Step 3: Create or Migrate a Skill

**Create a new skill (from your project directory):**
```bash
cd ~/example_project
kitty new data-analysis
# → Creates SKILL.md boilerplate in ~/.kitty/skills/data-analysis/
# → Automatically creates symlinks in .claude/skills/ and .agents/skills/
# → Automatically performs a git commit
```

**Migrate an existing directory (from your project directory):**
```bash
cd ~/example_project
# If .claude/skills/data-analysis/ is already a real directory
kitty migrate data-analysis
# → Moves it to ~/.kitty/skills/ and commits
# → Replaces original directory with a symlink
# → Creates symlinks for other providers automatically
```

> `migrate` and all commands involving symlinks must be executed in the project root because provider paths are workspace-relative by default.

---

## Command Reference

### Initialization

```bash
kitty init --global          # Initialize ~/.kitty/ global store (Once per machine)
kitty init                   # Initialize current workspace (Idempotent, run in project root)
```

### Skill Management

```bash
kitty new <skill>            # Create new skill and link to all providers
kitty link [<skill>]         # Create symlinks for an existing skill
  --provider claude|gemini   # Link only to a specific provider
  --force                    # Overwrite incorrect symlinks
kitty unlink <skill>         # Remove symlinks (does not delete the skill itself)
  --provider claude|gemini   # Uninstall only from a specific provider
kitty migrate <skill>        # Migrate a real directory to global store (run in project root)
  --from claude|gemini       # Specify authoritative source if providers differ
```

### Inspection

```bash
kitty status [<skill>]       # Three-way status: local changes / symlink health / remote diff
kitty list [local|remote]    # List all skills locally or on remote
```

### Multi-machine Sync (Requires remote config)

```bash
kitty fetch [<skill>]        # Fetch remote latest refs without modifying worktree
kitty checkout <skill>       # Overwrite local with remote version (destructive, auto-snapshot)
kitty push [<skill>]         # Commit local changes and push to remote
  --force                    # Force push to remote (uses --force-with-lease)
kitty clone <skill>          # Clone skill from remote for the first time and link to workspace
```

---

## Typical Workflow

### Daily Iteration

```bash
cd ~/example_project

# Edit skill in any editor
vim ~/.kitty/skills/data-analysis/SKILL.md
# Or modify through Claude/Gemini UI — changes are reflected in ~/.kitty/ via symlink

# Check status
kitty status
# ~/.kitty global store:
#   data-analysis   modified (SKILL.md)
# Workspace symlinks:
#   data-analysis   claude:✓  gemini:✓
# Remote: 1 unpushed commit

# Commit and Push
kitty push data-analysis
# Committed 'data-analysis' [example_project] 2026-03-25T10:31:44Z
# Pushed to origin/main ✓
```

### Fetching Skills on a New Machine

```bash
kitty init --global
# Configure remote (edit ~/.kitty/config.json, set "remote": "git@github.com:...")

cd ~/another_example_project
kitty init
kitty clone data-analysis
# Cloned 'data-analysis' from remote.
# Linked [claude, gemini]
```

### When Remote has Updates

```bash
kitty fetch
# data-analysis   remote 2 commit(s) ahead → `kitty checkout data-analysis`

kitty checkout data-analysis
# Auto-snapshot: committing 1 uncommitted file(s) before overwrite...
# Updated 'data-analysis' (2 commit(s) applied).
# All provider symlinks updated automatically.
```

### Handling Push Conflicts

```bash
kitty push data-analysis
# Push rejected: remote has divergent changes.
# --- Diff (remote vs local) ---
# ...
# Options:
#   kitty push --force data-analysis   Overwrite remote
#   kitty checkout data-analysis       Discard local, use remote version
```

---

## Configuration

### Global Configuration `~/.kitty/config.json`

```json
{
  "version": 1,
  "remote": "git@github.com:yourname/skills.git",
  "providers": {
    "claude": ".claude/skills",
    "gemini": ".agents/skills",
    "codex":  ".agents/skills"
  },
  "default_providers": ["claude", "gemini"],
  "commit_author": { "name": "kitty", "email": "kitty@local" }
}
```

- `remote: null` — Offline mode, all network operations are skipped gracefully.
- Provider paths support three formats:
  - `.claude/skills` — Workspace relative (Default, run in project root).
  - `~/...` — Home relative (Globally shared, skills visible to all projects).
  - `/absolute/path` — Absolute path.

### Workspace Configuration `.kitty/config.json`

```json
{
  "version": 1,
  "providers": ["claude"]
}
```

Overrides enabled providers for the current workspace (Inherits global `default_providers` if empty).

### `.kittyignore`

Uses same syntax as `.gitignore` to control which files are not tracked by kitty:

```
*.log
.DS_Store
node_modules/
.env
```

---

## Safety Mechanisms

**Auto-Snapshot Before Destructive Operations**

Before running `kitty checkout` (overwriting local), if there are uncommitted local changes, kitty automatically creates a commit to ensure a recovery point is available in git reflog.

**Recovering from Mistakes**

```bash
git -C ~/.kitty reflog                                        # View history anchors
git -C ~/.kitty checkout <hash> -- skills/data-analysis/      # Restore to specific version
```

**Auto-Diff Before Push**

When a `kitty push` is rejected by the remote, it automatically fetches and displays the differences, avoiding silent overwrites of others' work.

---

## Project Structure

```
~/.kitty/
├── .git/                 # Standard git repository
├── skills/
│   ├── data-analysis/
│   │   └── SKILL.md
│   └── trading-bot/
│       └── SKILL.md
├── .kittyignore
└── config.json
```

```
~/example_project/
├── .kitty/
│   └── config.json       # Workspace-level provider override (Optional)
├── .kittyignore
├── .claude/
│   └── skills/
│       └── data-analysis  →  ~/.kitty/skills/data-analysis
└── .agents/
    └── skills/
        └── data-analysis  →  ~/.kitty/skills/data-analysis
```
