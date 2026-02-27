# joytrunk onboard

初始化本地配置与工作区（创建 `~/.joytrunk`、config、workspace）。

## 用法

```bash
joytrunk onboard
```

## 说明

- 首次运行（本地尚无 `~/.joytrunk/config.json` 或其中没有有效的 **cli.locale**）时，会提示选择 CLI 语言：**zh**（中文）或 **en**（英文），直接回车即默认 **zh**；选择结果会写入 config 的 **cli.locale**。
- 若本地已有语言配置（config 存在且 **cli.locale** 为 zh 或 en），则直接创建/更新目录与 config，不再询问语言。
- 在用户主目录下创建 **JoyTrunk 根目录**（Linux/macOS：`~/.joytrunk`，Windows：`%USERPROFILE%\.joytrunk`）。
- 创建 **config.json**（默认配置）与 **workspace** 目录（含 `workspace/skills`、`workspace/memory`，不创建 `workspace/templates`）。
- 交互简洁，无需复杂配置。
- 完成后可提示在浏览器打开 http://localhost:32890 进行员工配置与网页管理；若尚未启动本地服务，需先执行 `joytrunk gateway`。

## 后续步骤

1. 执行 `joytrunk gateway` 启动本地管理后端（若未启动）。
2. 在浏览器打开 http://localhost:32890，创建员工、团队与设置。
3. 使用 `joytrunk chat` 与员工对话。

## 参见

- [gateway](gateway.md) — 启动本地管理后端
- [index](index.md) — 命令指南首页
