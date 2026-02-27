# JoyTrunk CLI

`joytrunk` 命令行入口：初始化、与员工对话、管理员工、可选启动本地管理后端。

## 安装（仓库内开发）

在仓库根目录（nanobot）下，对 cli 做可编辑安装（PowerShell）：

```powershell
cd cli
pip install -e ".[dev]"
```

然后可直接使用：

```powershell
joytrunk --help
joytrunk onboard
joytrunk chat
```

## 主要命令

| 命令 | 说明 |
|------|------|
| `joytrunk onboard` | 初始化 ~/.joytrunk、全局 config.json、workspace |
| `joytrunk chat` | 与员工对话（TUI：列出员工，最后一项为「新建员工」；不依赖 gateway） |
| `joytrunk employee` | 员工管理 TUI；`employee list` / `employee new` / `employee set <id> --name ...` |
| `joytrunk status` | 查看根目录、gateway URL、员工列表（从各员工 config 读取） |
| `joytrunk gateway` | 启动本地管理后端（端口 32890，供网页/UI 使用，可选） |
| `joytrunk language [zh\|en]` | 配置 CLI 界面语言 |
| `joytrunk docs` | 打开命令指南（`--local` 本地查看） |

## 配置与路径

- **全局配置**：`~/.joytrunk/config.json` **仅保留全局配置**（ownerId、gateway、agents.defaults、channels、providers、cli.locale 等），不包含员工列表。
- **每位员工作为独立 agent**：各自使用 **`~/.joytrunk/workspace/employees/<employee_id>/config.json`**，存放该员工身份（id、ownerId、name、persona、role 等）及可选的 `agents`、`providers` 覆盖（覆盖全局配置）。员工列表由扫描 `workspace/employees/` 下各目录的 config.json 得到。
- **路径**：Windows `%USERPROFILE%\.joytrunk`（PowerShell: `$env:USERPROFILE\.joytrunk`）；Linux/macOS `~/.joytrunk`。工作区含 `workspace/skills/`、`workspace/memory/`、`workspace/employees/<id>/`；模板仅存于 joytrunk 包内。

## 开发/测试：cli 目录下的 .env

在 **cli 主目录**（即本仓库的 `cli/` 目录，非 `~/.joytrunk/workspace`）可放置 `.env` 文件，写入 API Key 等配置。执行 `joytrunk onboard` 时，若检测到该目录下存在**有效的** `.env`（至少包含一个可导入变量且值非空），会提示是否将配置导入到 `~/.joytrunk/config.json`，便于本地测试整个项目。可选变量见 `cli/.env.example`（如 `OPENAI_API_KEY`、`OPENAI_API_BASE_URL`、`OPENAI_MODEL`、`JOYTRUNK_ROUTER_URL` 等）。`.env` 已由仓库根目录 `.gitignore` 忽略，请勿提交密钥。

## 测试

```powershell
cd cli
pip install -e ".[dev]"
pytest -v
```

## 命令指南文档

- 文档源位于 `joytrunk/docs/`（Markdown），随包分发。
- 用户可通过 `joytrunk docs` 打开官网命令指南，或 `joytrunk docs --local` 本地查看；`joytrunk docs --path` 打印文档目录。
