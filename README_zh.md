# Kitty

一个“单源 + 复制分发”的 AI Skill 管理工具。

Kitty 把权威 skill 统一放在 `~/.kitty/skills/`，然后把内容**复制**到：

- `~/.claude/skills/`
- `~/.agents/skills/`
- `~/.codex/skills/`

这一版不使用 symlink，也不区分项目工作区。

## 核心模型

1. 唯一权威源：`~/.kitty/skills/<skill>/`
2. 复制分发：`kitty distribute <skill>`
3. 用 `kitty status` 检查一致性与修改状态

## 安装

前置条件：

- Python 3.9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

本地源码安装：

```bash
uv tool install .
```

如有需要，请确保 `~/.local/bin` 在 `PATH` 中。

## 命令

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

- 全局幂等初始化。
- 确保 `~/.kitty` 下必需文件存在：
  - `.kittyignore`
  - `config.json`
  - `manifest.yaml`
  - `skills/`
- 同时确保用户目录下 provider 路径存在。

### `kitty new <skill>`

- 创建 `~/.kitty/skills/<skill>/SKILL.md`
- 可选：`-f path/to/xx.md`，将该文件内容作为 `SKILL.md`
- 更新 `manifest.yaml`
- skill 命名规则：只允许小写字母、数字、`-`

### `kitty migrate path/to/skill_dir`

- 将现有目录导入到 `~/.kitty/skills/`
- 使用源目录名作为 skill 名
- 如果 kitty 中已有同名 skill，会给出警告并跳过，避免覆盖

### `kitty edit <skill> [typora|antigravity]`

- 打开 `~/.kitty/skills/<skill>` 目录进行编辑。
- 不传 editor 时，读取 `config.json` 的 `default_editor`。

### `kitty distribute <skill>`

- 将 `~/.kitty/skills/<skill>` 复制到所有 provider 目录。
- 本版本不提供 `--provider`。
- 分发后会更新 `manifest.yaml` 中的 hash 信息。

### `kitty status`

显示：

- `SYNCED`：当前 skill 是否在所有 provider 保持同步
- `PENDING_SYNC`：相对上次 distribute 是否有 canonical 改动未分发
  - `yes`：已修改但未分发
  - `no`：无未分发改动
- `LAST_MODIFIED`：canonical skill 目录的最后本地修改时间
- 各 provider 状态：
  - `synced`
  - `changed`
  - `missing`
  - `invalid`

## 默认目录结构

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

## 备注

- `manifest.yaml` 作为 skill 索引与状态文件使用。
- 如需测试或迁移，仍可覆盖工作区路径：
  - `--workspace <path>`
  - `KITTY_WORKSPACE=<path>`
