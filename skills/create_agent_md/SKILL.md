---
name: create-agent-md
description: 按计划或需求完善 JoyTrunk 的 agent.md（Agent 蓝图）。在用户提供计划、待办或具体修改要求时，对 agent.md 做增量修改并勾选 todo，不修改 product.md 或计划文件。
---

# 完善 agent.md（JoyTrunk Agent 蓝图）

## 何时使用

- 用户说「按计划完善 agent.md」「按计划实施 agent.md」「完成 agent.md 的 xxx」或附带了 agent.md 的修改计划（含 § 节号或待办列表）时使用本 skill。
- 仅修改 [agent.md](e:\Documents\NKU\duochouchouai\nanobot\agent.md)，不修改 product.md 或任何 .plan.md 计划文件。

## agent.md 文档结构（速查）

| 节 | 内容 |
| --- | --- |
| §1 | 项目概述（项目名、一句话、目标用户、运行平台、安装与发布等） |
| §2 | 技术栈与架构（cli/vue/nodejs、PyPI/pip、Mermaid 图） |
| §3 | cli / vue / nodejs 功能细化 |
| §4.1 | 入口命令（joytrunk 由 pip 安装的 Python 包提供，默认端口 32890） |
| §4.2 | 配置与工作区路径（~/.joytrunk，跨平台路径） |
| §4.3 | 多员工 workspace（employees/<employee_id>/，path.join 跨平台） |
| §4.4 | onboard（提示打开 http://localhost:32890） |
| §4.5 | 大模型接入与计费 |
| §4.6 | 测试 |
| §4.7 | 发布与本地管理端口（PyPI、32890） |
| §5 | 当前进度 |
| §6 | 开发约定（CLI 技术选型 Python、终端示例 PowerShell、跨平台） |

## 执行流程

1. **确认范围**：从用户消息或附件计划中提取要改的节（如 §1、§4.2、§6）和每条修改的要点。
2. **待办**：若已有 todo 列表，从第一个起标为 `in_progress`，做完一条再标 `completed`，直到全部完成；不要新建重复 todo。
3. **增量修改**：用 search_replace 在 agent.md 中按计划逐条修改，保留原有措辞与格式，只增补或替换指定内容。
4. **不改动**：不编辑 product.md、不编辑任何 .plan.md 文件。

## 常见修改类型

- **§1 项目概述**：在列表末尾或「运行平台」后新增一条（如「安装与发布」「运行平台」），或扩写现有条。
- **§2 技术栈**：在首段后增加 pip 分发、端口等约束；在 Mermaid 图前后增加说明或新图。
- **§4.1**：补充「由 pip 安装的 Python 包提供」、entry_points、默认端口 32890。
- **§4.2**：补充 Linux/macOS 与 Windows 路径写法、平台无关解析（Path.home() / os.homedir()）。
- **§4.3**：补充两平台含义相同、使用 path.join 等保证路径分隔符正确。
- **§4.4**：补充 onboard 完成后提示打开 http://localhost:32890。
- **§4.7**：新增小节，写发布方式（PyPI、pip）、默认本地管理端口 32890。
- **§6 开发约定**：修改「CLI 技术选型」为 Python（pip 分发）、写清与 Node 后端关系（由 Python 启动或 Python 托管 Vue）。

## 约定

- 路径示例：文档通用写法用 `~/.joytrunk`，Windows 等价注明 `%USERPROFILE%\.joytrunk` 或 PowerShell `$env:USERPROFILE\.joytrunk`。
- 默认本地管理端口：**32890**，统一写 http://localhost:32890。
- 安装方式：**pip install joytrunk**，包名 joytrunk，CLI 入口 joytrunk / joytrunk onboard。
