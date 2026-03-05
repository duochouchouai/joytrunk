<div align="center">
  <h1>JoyTrunk</h1>
  <p><strong>本地 24/7 智能体团队 — 你是负责人，他们是你的员工。</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
    <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey" alt="Platform">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

**JoyTrunk** 是一款本地、24/7 运行的智能体团队产品：你作为**负责人**，管理一个或多个**员工**（AI 智能体）。通过即时消息与他们互动，他们完成任务并汇报。产品面向 **Linux 与 Windows**，通过 **pip** 以开源包形式分发。

---

## 核心概念

- **负责人–员工模型**：员工由单一负责人创建并归属其下，共同组成 **JoyTrunk 团队**。关系不可转移。
- **多员工**：一名负责人可拥有多名员工，具备不同角色、性格与能力。
- **渠道**：JoyTrunk 自有网页 IM（Vue）与 CLI；可选第三方渠道（如飞书、QQ、Telegram）。
- **员工生存规则**：员工不得向他人泄露负责人的主机或敏感信息；仅能以脱敏、隐私保护的方式协助他人。

---

## 快速上手

从安装到对话（CLI 或网页），按此处说明即可。配置根目录：**Linux/macOS** `~/.joytrunk`；**Windows** `%USERPROFILE%\.joytrunk`。

**1. 安装** — `pip install joytrunk`，或从仓库：`cd cli && pip install -e ".[dev]"`

**2. 初始化（仅首次）** — `joytrunk onboard`

**3. 构建 Web 界面（仅首次，若要用浏览器）** — `cd cli/joytrunk/ui && npm install && npm run build`。仅用 CLI 可跳过。

**4. 启动 server 与 gateway（两个终端）** — 网页或 CLI 对话前两者都需运行。终端 1：`joytrunk server`（http://localhost:32890，需 Node.js 18+）。终端 2：`joytrunk gateway`（127.0.0.1:32891，A2A）。

**5. 使用产品** — **CLI**：`joytrunk chat`（TUI）。**网页**：打开 http://localhost:32890（员工、对话、聊天记录、日志、记忆、设置）。Vue 开发：`joytrunk server` + `cd cli/joytrunk/ui && npm run dev` → http://localhost:32893。

**English**: See [README.md](../README.md).

---

## LLM 与计费

- **默认**：请求经 **JoyTrunk Router**（默认模型 **MINIMAX-M2.1**；无需 API Key）；按量计费。
- **可选**：负责人可在本地管理界面配置**自有 LLM**（API Key、Base URL、模型）。此时请求直连负责人端点，不由 JoyTrunk 计费。

---

## 架构

- **CLI**（Python）：入口 `joytrunk`，命令包括 `onboard`、**`chat`**（TUI：列出/选择或新增员工后对话；**gateway** 运行时走 A2A）、**`employee`**（list/new/set）、**`server`**（本地后端 32890 + 托管内置 Vue UI）、**`gateway`**（32891 A2A，网页与 CLI 对话需经其进入 agent 循环）、`gateway status`、`status`、`language`、`docs`、**`memory`**、**`log`**。配置：全局 `~/.joytrunk/config.json`；每员工 `~/.joytrunk/workspace/employees/<id>/config.json`。
- **Vue**（本地管理 UI）：源码 `cli/joytrunk/ui`，构建输出 `cli/joytrunk/server/static`。由 `joytrunk server` 在 **http://localhost:32890** 提供。页面：首页、对话、员工（列表/创建/编辑）、每员工**日志**、**聊天记录**（含内联输入）、**记忆**（分类/条目）、设置（自定义 LLM、用量）。仅与本地 server 通信。
- **Node.js**（官方后端）：云服务 — 用户注册、JoyTrunk IM、**LLM Router**（默认模型 MINIMAX-M2.1）、计费。与本地 32890 server 分离；用于账号绑定或使用 Router 调用 LLM。

本地流程：**CLI** + **joytrunk server**（API + Vue）+ **joytrunk gateway**（A2A）。网页与 CLI 对话均经 gateway 进入员工 agent 循环。

---

## 仓库结构

| 目录 | 作用 |
|------|------|
| **cli/** | Python 包 `joytrunk`：CLI 入口、`onboard`、`chat`（TUI）、`employee`、`server`（Node 后端 32890 + 从 `cli/joytrunk/server/static` 提供 Vue）、`gateway`（32891 A2A）、`memory`、`log`、`status`、`language`、`docs`。本地 UI 源码：`cli/joytrunk/ui`；构建输出：`cli/joytrunk/server/static`。安装：`pip install -e ./cli`。 |
| **vue/** | **仅官方站**：Vue 3 + Vite（产品页、文档、定价、认证）。开发：`npm run dev`（端口 32892）。本地管理 UI 在 **cli/joytrunk/ui**，不在此。 |
| **nodejs/** | 官方后端（用户注册、IM、LLM Router、计费）。`npm install && npm start`（默认端口 32891）。 |
| **readme/** | [README_zh.md](README_zh.md) — 中文说明。 |

---

## 开发（develop 分支）

开发者基于 **`develop`** 分支协作。以下步骤从克隆到运行与测试。

### 环境要求

- **Node.js** 18+（后端与前端）
- **Python** 3.11+（CLI）
- **Conda**（Windows 推荐；Linux/macOS 可选）用于独立 CLI 环境

### 克隆与分支

```bash
git clone <repo-url>
cd joytrunk
git checkout develop
```

### 1. CLI（joytrunk）

使用独立 conda 环境，便于 `joytrunk` 命令与测试隔离运行：

```powershell
# Windows (PowerShell)
conda create -n joytrunk python=3.11 -y
conda activate joytrunk
cd cli
pip install -e ".[dev]"
joytrunk onboard
```

```bash
# Linux / macOS
conda create -n joytrunk python=3.11 -y
conda activate joytrunk
cd cli && pip install -e ".[dev]" && joytrunk onboard
```

- **运行 CLI**：`joytrunk`、`joytrunk docs`（打开命令指南）、`joytrunk status`、**`joytrunk chat`**（TUI：列出/选择或新增员工后对话；对话需 **joytrunk gateway** 已运行）、**`joytrunk employee`**（list/new/set）、**`joytrunk gateway`** / **`joytrunk gateway status`**、**`joytrunk memory`**、**`joytrunk log`**
- **运行本地 server**（供 Web UI）：`joytrunk server`（后端 32890；首次运行会安装 Node 依赖）
- **运行测试**：`pytest -v`（在 `cli/` 下）

### 2. 本地 server（32890，或 UI 开发时 32893）

**本地管理后端**由 CLI 启动，托管**内置本地 UI**（源码 `cli/joytrunk/ui`，构建输出 `cli/joytrunk/server/static`）：

```bash
joytrunk server
```

- 监听 **http://localhost:32890**。即单一进程：API + 静态 UI。
- 提供 REST API 与 SPA（员工、团队、设置、对话、日志、记忆）。需 PATH 中有 **Node.js** 18+。
- **端口 32893（仅 Vue 开发）**：前端热更新时，在第二个终端运行 `cd cli/joytrunk/ui && npm run dev`（32890 上仍运行 `joytrunk server`）。Vite 开发服务器监听 **http://localhost:32893**，并将 `/api` 代理到 32890。仅开发本地 UI 时使用 32893；生产使用 32890。

### 3. 官方站前端（Vue，可选）

仅当开发或部署**官方站**时：

```bash
cd vue
npm install
npm run dev
```

- 开发服务器端口 **32892**，API 代理到 32891。需先启动 **nodejs** 后端。
- **vue/** 仅为官网；**本地管理 UI** 在 **cli/joytrunk/ui**，由 `joytrunk server` 提供。

### 4. 官方后端（nodejs，可选）

云服务（用户注册、IM、LLM Router、计费）：

```bash
cd nodejs
npm install
npm start
```

- 运行**官方后端**（默认端口 32891），非本地 32890 server。
- 用于部署**官方站**或用户绑定 JoyTrunk 账号时。

### 全栈（本地）

要运行全栈（CLI、Web UI 或 Vue 开发），请按上文**快速上手**操作。

### 约定与更多

- **约定**：[agent.md](../agent.md) 定义路径、配置结构、工作区布局、测试及 PowerShell 优先的命令示例。
- **产品**：[product.md](../product.md) 定义产品与负责人–员工模型。
- **多智能体**：多人或多智能体并行协作时，参见 [agent.md](../agent.md) 中的协作说明以避免冲突。

---

## 文档

| 文档 | 说明 |
|------|------|
| [readme/README_zh.md](README_zh.md) | 中文说明（安装、server、gateway、对话、Vue UI、日志）。 |
| [readme/websocket.md](websocket.md) | 官网–CLI WebSocket 链路：绑定、/ws/cli、/ws/im、task_result、joytrunk_reply 及故障排查。 |
| [product.md](../product.md) | 产品定义（负责人–员工模型、本地 UI 与官方站、流程、MVP、生存规则、默认模型 MINIMAX-M2.1）。 |
| [agent.md](../agent.md) | 实现蓝图（cli/vue/nodejs、双后端、路径、入驻、进度）。 |
| **CLI 命令指南** | `joytrunk docs` 打开在线指南；`joytrunk docs --local` 打开本地。源码：`cli/joytrunk/docs/`。 |

---

## 参与贡献

欢迎贡献。当前路线图与实现状态见 [agent.md](../agent.md)。

---

<p align="center">
  <sub>JoyTrunk 在本仓库中完成规格与设计。代码库中还包含 <strong>nanobot</strong>，作为设计与架构参考；JoyTrunk 作为独立产品实现，运行时不依赖 nanobot。</sub>
</p>
