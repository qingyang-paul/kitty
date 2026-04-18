Kitty 再版设计



核心需求：skill备份+跨平台同步+便捷

we use hard copy!



Remote <-> local global <-> agents' global skill space (~/.claude/skills & ~/.agents/skills/ & ~/.codex/skills/)



Command:

`Init`:  

- make local global space (check first)
- config remote repo
- Make provider skill space (if not exists)



`new <skill-name>`

- Make skill directory wth SKILL.md in kitty
- SKILL.md template contains yaml header (name, description)
- Print path in the command line so user can vim directory.

- Optional `-f xx.md` ，extract filename as skill name, register skill with xx.md as SKILL.md

- new时就做合法性校验比如 skill 名规则：

  - 只允许小写字母、数字、-
  - 禁止空格
  - 禁止和已有 skill 重名



`import path/to/<skill-name>`

- 检查目录是否合法
- 拷贝到 kitty global space
- 补齐/校验 SKILL.md
- 注册到 manifest
- 后续都以 kitty 里的版本为 canonical
- auto completion on skill name 





`distribute <skill-name> `  

- copy this version to all providers' skill space and the kitty space
- get file hash for comparison in status commad
- `-m message (optional)`: add message
- use default message if -m message is empty (update  <skill-name> skill)
- git add in kitty local global space, and commit.
- push to remote repo



`list`

- Show all available skills under local global space



`status`

- which skill is needed to be distrubute (changed, or inconsistent across providers)

  





轻量的 manifest，比如：

```yaml
skills:
  my-skill:
    canonical_path: skills/my-skill
    tracked: true
    providers:
      claude:
        path: ~/.claude/skills/my-skill
        last_distributed_hash: xxx
      codex:
        path: ~/.codex/skills/my-skill
        last_distributed_hash: yyy
    source: new
    updated_at: 2026-04-17T22:00:00Z
```



1. 这一版本里采用复制，不使用任何symlink
2. init 不用global参数，在任何时候，任何地点，先检查是否有~/.kitty , 以及.kitty里是不是有.kittyignore, config.json, manifest 等必须文件；如果已经有全局文件，则不用再init
3. 这一版本里kitty不再区分项目路径，所有skills 就放在用户根目录下，监控的是 ~/.claude/skills, ~/.agents/skills, ~/.codex/skills/ 目录。所以也没有项目下的Init
4. distribute 不再添加--provider参数，kitty为唯一skill源
5. 添加edit 命令， edit <skill-name> 带自动补全，参数可选typora或者antigravity，打开对应的文件夹（~/.kitty/路径下) 
6. status要显示是否修改过
