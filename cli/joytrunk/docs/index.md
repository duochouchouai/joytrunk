# JoyTrunk 命令指南

JoyTrunk（喜象 Agent）是一款部署在用户本地的、7×24 小时运行的智能体员工；负责人通过即时通讯与员工交互完成日常工作。

## 安装

```bash
pip install joytrunk
```

支持 Windows / Linux / macOS。安装后获得 `joytrunk` 命令行入口。

## 快速开始

1. **初始化配置与工作区**：`joytrunk onboard`
2. **与员工对话**：`joytrunk chat`（从 config.json 读取员工列表，无需先启动 gateway）
3. **查看/新增/设置员工**：`joytrunk employee` 或 `joytrunk employee list` / `joytrunk employee new` / `joytrunk employee set <id> --name ...`
4. **查看状态**：`joytrunk status`（从 config.json 读取）
5. **可选**：`joytrunk gateway` 启动本地后端，供网页/Electron 等 UI 使用（目前仅 TUI 时可不启动）

## 命令列表

| 命令 | 说明 |
|------|------|
| [joytrunk onboard](onboard.md) | 初始化本地配置与工作区（~/.joytrunk） |
| [joytrunk gateway](gateway.md) | 启动本地管理后端（默认 32890，供网页/UI 使用，仅保留） |
| [joytrunk chat](chat.md) | 与员工对话（从 config 与 workspace 读取，TUI 列出员工，最后一项为新建） |
| [joytrunk employee](employee.md) | 查看、新增、设置员工（config.json） |
| [joytrunk status](status.md) | 查看运行状态与员工列表（从 config.json 读取） |
| joytrunk language | 配置 CLI 界面语言（中文 / 英文） |
| joytrunk docs | 打开本命令指南（官网或本地） |

使用 `joytrunk --help` 查看所有命令；`joytrunk <命令> --help` 查看该命令参数。

## 配置

**所有配置均在 `~/.joytrunk/config.json`**，包括员工列表与负责人 ID；不再使用 store.json。CLI 的 chat、employee、status 均直接读写 config.json，无需连接 gateway。

## CLI 界面语言

运行 `joytrunk language` 查看当前语言；`joytrunk language zh` 设为中文，`joytrunk language en` 设为英文。设置写入 `~/.joytrunk/config.json` 的 `cli.locale`。也可通过环境变量 `JOYTRUNK_LANG=zh` 或 `JOYTRUNK_LANG=en` 临时覆盖。

## 大模型

默认使用 **JoyTrunk Router**，无需配置 API Key；默认模型为 **MINIMAX-M2.1**。高级用户可在本地管理界面配置自有 LLM。

## 文档版本

本文档与 JoyTrunk CLI 版本一致，随包发布。官网命令指南由同一文档源构建部署。
