# Changelog

All notable changes to the JoyTrunk CLI project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-03

### Added

- **正式开源**：JoyTrunk CLI 以 MIT 许可完整开源；本仓库仅包含 CLI 及本地服务（本地 server + 内置 Web UI）。
- **CLI 命令**：`joytrunk`、`joytrunk onboard`、`joytrunk chat`（TUI）、`joytrunk employee`、`joytrunk server`、`joytrunk gateway`、`joytrunk status`、`joytrunk memory`、`joytrunk log`、`joytrunk docs`、`joytrunk language` 等。
- **本地服务**：`joytrunk server`（REST API + Vue 管理界面，端口 32901）、`joytrunk gateway`（A2A 对话网关，端口 32900）。
- **多员工与记忆**：多智能体员工、每员工独立配置与记忆、会话历史、TUI 与 Web 双端对话。
- **自有 LLM**：支持 OpenAI 兼容 API（`OPENAI_API_KEY` / `OPENAI_API_BASE_URL` / `OPENAI_MODEL`）及可选 JoyTrunk Router；配置可通过 `cli/.env` 在 onboard 时导入。
- **平台**：支持 Linux 与 Windows；Python 3.11+，Node.js 18+（用于本地 server 与 UI）。

### Changed

- **仓库范围**：官网前端（Vue）与云后端（Node）已迁出至独立私有仓库；README、agent.md、.gitignore 已同步为「仅 CLI 开源」表述。
- **版本与分类**：版本号从 0.1.0 升级为 1.0.0；PyPI 分类为 Production/Stable。

### Removed

- 本仓库中不再包含 `vue/`、`nodejs/`、`bridge/` 目录；相关能力由独立私有仓库维护。

[1.0.0]: https://github.com/duochouchouai/nanobot/releases/tag/v1.0.0
