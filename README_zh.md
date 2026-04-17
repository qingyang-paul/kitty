# Kitty

**跨 Agent、跨 Workspace 的 AI Skill 版本管理器**

---

## 背景

现代 AI 开发中，同一套 skills 往往需要同时服务多个 Agent：

| Agent | Skills 路径 |
|---|---|
| Claude | `.claude/skills/` |
| Gemini | `.agents/skills/` |
| Codex | `.codex/skills/` |

这带来了一个持续的麻烦：你在某个项目里迭代优化了一个 skill，但另一个项目的 Claude 还在用老版本；Gemini 和 Claude 各自有一份副本，内容开始漂移；换到新机器后得手动把所有 skill 重新配置一遍。

Kitty 解决这个问题。

---

## 设计思路

**单副本 + Symlink + Git**

```
~/.kitty/skills/data-analysis/   ← 唯一权威副本（git 管理）
        │
        ├──→ ~/example_project/.claude/skills/data-analysis   (symlink)
        └──→ ~/example_project/.agents/skills/data-analysis   (symlink)
```

- `~/.kitty/` 是一个标准 git 仓库，所有 skill 存在这里
- 各 provider 目录里存放的是 symlink，而不是文件副本
- 修改任意一处，所有 provider 立即看到更新，无需手动同步
- provider 路径默认为 **workspace 相对路径**（`.claude/skills`），在项目目录下执行命令即可

`kitty sync` 不存在：symlink 架构让"谁和谁同步"这个问题在结构层面消失了。

---

## 安装

### 前置条件

- Python 3.9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)（推荐）或 pip

### 用 uv 安装（推荐）

从 GitHub 直接安装：

```bash
uv tool install git+https://github.com/qingyang-paul/kitty.git
```

或克隆后本地安装：

```bash
git clone https://github.com/qingyang-paul/kitty.git ~/kitty
cd ~/kitty
uv tool install .
```

### 注册进环境变量（PATH）

`uv tool install` 会把可执行文件放到 `~/.local/bin/`。如果 `kitty` 命令找不到，把这一行加进你的 shell 配置：

```bash
# ~/.zshrc 或 ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

然后重新加载：

```bash
source ~/.zshrc   # 或 source ~/.bashrc
```

验证安装：

```bash
kitty --help
```

### Shell 命令补全（可选）

kitty 支持对 skill 名称和 provider 名称进行 Tab 自动补全。

**zsh**
```bash
mkdir -p ~/.zfunc
_KITTY_COMPLETE=zsh_source kitty > ~/.zfunc/_kitty
echo 'fpath=(~/.zfunc $fpath)' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
source ~/.zshrc
```

**bash**
```bash
mkdir -p ~/.bash_completion.d
_KITTY_COMPLETE=bash_source kitty > ~/.bash_completion.d/kitty
echo '[[ -f ~/.bash_completion.d/kitty ]] && source ~/.bash_completion.d/kitty' >> ~/.bashrc
source ~/.bashrc
```

**fish**
```bash
_KITTY_COMPLETE=fish_source kitty > ~/.config/fish/completions/kitty.fish
```

> **注意**：macOS 自带一个叫 `kitty` 的终端模拟器，如果发生冲突，可以把 `~/.local/bin` 放在 PATH 最前面（如上），或者将本工具的入口点改名为 `sk`（修改 `pyproject.toml` 中的 `[project.scripts]`）。

### 更新工具

#### 如果从 GitHub 安装

直接执行：

```bash
uv tool upgrade kitty
```

#### 如果从本地源码安装

进入克隆目录执行安装命令即可：

```bash

# 进入目录并拉取最新代码
cd ~/kitty
git pull

# 重新安装（--force 覆盖已有版本）
uv tool install . --force
```

一行完成：

```bash
cd ~/kitty && git pull && uv tool install . --force
```

---

## 快速上手

### 第一步：初始化全局存储（每台机器一次）

```bash
kitty init --global
```

创建 `~/.kitty/`（git 仓库）、默认 `config.json` 和 `.kittyignore`。

### 第二步：在项目里初始化 Workspace

```bash
cd ~/example_project
kitty init
```

创建 `.kitty/config.json`，并在项目目录下为 Claude、Gemini 准备好 skills 目录。

### 第三步：创建或迁移 skill

**新建 skill（在项目目录下执行）：**
```bash
cd ~/example_project
kitty new data-analysis
# → 在 ~/.kitty/skills/data-analysis/ 创建 SKILL.md 脚手架
# → 自动在 .claude/skills/ 和 .agents/skills/ 创建 symlink
# → 自动 git commit
```

**迁移已有目录（在项目目录下执行）：**
```bash
cd ~/example_project
# 如果 .claude/skills/data-analysis/ 已经是一个真实目录
kitty migrate data-analysis
# → 将其移入 ~/.kitty/skills/ 并 commit
# → 原目录替换为 symlink
# → 其他 provider 同步创建 symlink
```

> `migrate` 和所有涉及 symlink 的命令需要在项目根目录下执行，因为 provider 路径默认是 workspace 相对路径。

---

## 命令参考

### 初始化

```bash
kitty init --global          # 初始化 ~/.kitty/ 全局存储（每台机器一次）
kitty init                   # 初始化当前 workspace（幂等，在项目根目录执行）
```

### Skill 管理

```bash
kitty new <skill>            # 创建新 skill 并链接到所有 provider
kitty link [<skill>]                   # 为已有 skill 创建 symlink
  --provider claude|gemini|codex       # 只链接某个 provider
  --force                              # 覆盖指向错误的 symlink
kitty unlink <skill>                   # 删除 symlink（不删除 skill 本体）
  --provider claude|gemini|codex       # 只从某个 provider 卸载
kitty migrate <skill>                  # 将真实目录迁移进全局存储（在项目根目录执行）
  --from claude|gemini|codex           # 当多个 provider 内容不一致时指定权威来源
```

### 审查

```bash
kitty status [<skill>]       # 三向状态：本地修改 / symlink 健康 / remote 差距
kitty list [local|remote]    # 列出本地或远端的所有 skill
```

### 多机同步（需配置 remote）

```bash
kitty fetch [<skill>]        # 拉取 remote 最新 refs，不修改工作区
kitty checkout <skill>       # 用 remote 版本覆盖本地（破坏性，覆盖前自动快照）
kitty push [<skill>]         # 提交本地改动并推送到 remote
  --force                    # 强制覆盖 remote（使用 --force-with-lease）
kitty clone <skill>          # 首次从 remote 拉取 skill 并链接到 workspace
```

---

## 典型工作流

### 日常迭代

```bash
cd ~/example_project

# 在任意编辑器里修改 skill
vim ~/.kitty/skills/data-analysis/SKILL.md
# 或者通过 Claude/Gemini 的 UI 修改 — 因为 symlink，改动已反映在 ~/.kitty/

# 检查状态
kitty status
# ~/.kitty global store:
#   data-analysis   modified (SKILL.md)
# Workspace symlinks:
#   data-analysis   claude:✓  gemini:✓
# Remote: 1 unpushed commit

# 提交并推送
kitty push data-analysis
# Committed 'data-analysis' [my-trading-bot] 2026-03-25T10:31:44Z
# Pushed to origin/main ✓
```

### 在新机器上拉取 skill

```bash
kitty init --global
# 配置 remote（编辑 ~/.kitty/config.json，设置 "remote": "git@github.com:..."）

cd ~/another_example_project
kitty init
kitty clone data-analysis
# Cloned 'data-analysis' from remote.
# Linked [claude, gemini]
```

### Remote 有更新时

```bash
kitty fetch
# data-analysis   remote 2 commit(s) ahead → `kitty checkout data-analysis`

kitty checkout data-analysis
# Auto-snapshot: committing 1 uncommitted file(s) before overwrite...
# Updated 'data-analysis' (2 commit(s) applied).
# All provider symlinks updated automatically.
```

### 遇到推送冲突

```bash
kitty push data-analysis
# Push rejected: remote has divergent changes.
# --- Diff (remote vs local) ---
# ...
# Options:
#   kitty push --force data-analysis   覆盖 remote
#   kitty checkout data-analysis       放弃本地，用 remote 版本
```

---

## 配置

### 全局配置 `~/.kitty/config.json`

```json
{
  "version": 1,
  "remote": "git@github.com:yourname/skills.git",
  "providers": {
    "claude": ".claude/skills",
    "gemini": ".agents/skills",
    "codex":  ".codex/skills"
  },
  "default_providers": ["claude", "gemini", "codex"],
  "commit_author": { "name": "kitty", "email": "kitty@local" }
}
```

- `remote: null` — 单机模式，所有网络操作优雅跳过
- provider 路径支持三种格式：
  - `.claude/skills` — workspace 相对路径（默认，在项目根目录下执行命令）
  - `~/...` — home 相对路径（全局共享，skills 对所有项目可见）
  - `/absolute/path` — 绝对路径

### Workspace 配置 `.kitty/config.json`

```json
{
  "version": 1,
  "providers": ["claude"]
}
```

覆盖当前 workspace 启用的 provider 列表（留空则继承全局 `default_providers`）。

### `.kittyignore`

与 `.gitignore` 语法相同，控制哪些文件不被 kitty 追踪：

```
*.log
.DS_Store
node_modules/
.env
```

---

## 安全机制

**破坏性操作前自动快照**

执行 `kitty checkout`（覆盖本地）之前，若存在未提交的本地改动，kitty 会自动先执行一次 commit，确保 git reflog 里有可恢复的锚点。

**恢复误操作**

```bash
git -C ~/.kitty reflog                                        # 查看历史锚点
git -C ~/.kitty checkout <hash> -- skills/data-analysis/      # 恢复到指定版本
```

**推送前自动 diff**

`kitty push` 遭 remote 拒绝时，自动 fetch 并展示差异，不会静默覆盖他人改动。

---

## 项目结构

```
~/.kitty/
├── .git/                 # 标准 git 仓库
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
│   └── config.json       # workspace 级 provider 覆盖（可选）
├── .kittyignore
├── .claude/
│   └── skills/
│       └── data-analysis  →  ~/.kitty/skills/data-analysis
└── .agents/
    └── skills/
        └── data-analysis  →  ~/.kitty/skills/data-analysis
```
