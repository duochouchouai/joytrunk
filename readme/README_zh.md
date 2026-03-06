<div align="center">
  
  <img src="../imgs/logo.png" alt="JoyTrunk" width="120" />
  <h1>JoyTrunk</h1>
  <p><strong>你自己的 AI 团队。本地、私密、24/7。</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
    <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey" alt="Platform">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

<a href="../README.md">English</a>

> "像跟真人一样聊天，然后你的AI团队就把事情做完了"
> *Chat like with real people. Your AI team gets it done.*

**JoyTrunk** 让你在本地拥有一整支 AI 员工团队。你是负责人：创建不同角色与性格的员工，然后像和真人一样与他们对话——通过 CLI、本地网页或 App，也可通过飞书、QQ 等已有工具随时随地下达任务。说出你的需求，AI 团队就会完成：调研、写作、写代码、日常事务。一切留在本机，除非你主动连接云服务。

- **本地优先。** 配置、对话与记忆存放在 `~/.joytrunk`（Windows：`%USERPROFILE%\.joytrunk`）。你的团队，你做主。
- **多员工。** 同时运行多名员工，各有角色与风格；在 TUI 或网页聊天中切换。
- **CLI + 网页 + App。** 在终端用 `joytrunk chat`、内置 Vue 界面或 App。飞书、QQ 等渠道一键触达员工。
- **开源。** 通过 `pip` 安装；可扩展、自托管，无厂商锁定。

**环境要求：** Python 3.11+，Node.js 18+。

---

## 快速开始

按顺序完成以下步骤。第五步后即可在浏览器打开网页或在 CLI 中对话。

### 1. 安装

```bash
pip install joytrunk
```

或从本仓库安装：

```bash
cd cli
pip install -e ".[dev]"
```

### 2. 初始化

首次运行：

```bash
joytrunk onboard
```

会在 `~/.joytrunk` 下创建配置与工作区。可直接接受默认选项。

### 3. 构建网页界面

需要浏览器界面时执行一次；仅用 CLI 可跳过。

```bash
cd cli/joytrunk/ui
npm install
npm run build
```

`joytrunk server` 将提供该构建产物。拉取 UI 更新后按需重新构建即可。

### 4. 启动 server 与 gateway

需要两个终端；两者都保持运行才能对话。

**终端 1 — 本地 server**

```bash
joytrunk server
```

监听 http://localhost:32901。首次运行可能安装 Node 依赖，等待其报告已开始监听即可。

**终端 2 — A2A gateway**

```bash
joytrunk gateway
```

监听 127.0.0.1:32900。对话期间保持运行。

端口在 `cli/.env` 中配置：`JOYTRUNK_SERVER_PORT` 与 `JOYTRUNK_A2A_PORT`。

### 5. 使用 JoyTrunk

- **网页：** 打开 http://localhost:32901，创建员工后即可对话。其余交给 AI 团队。
- **CLI：** 在第三个终端运行 `joytrunk chat`，选择员工后在 TUI 中对话。gateway 须保持运行。
- **App：** 在手机上对话，并连接飞书、QQ 等平台，从常用工具里随时触达你的团队。

English: [README.md](../README.md)

---

## 当前在运行什么？

- **`joytrunk server`** — 在 32901 端口提供 Vue 应用与 REST API。
- **`joytrunk gateway`** — 在 32900 端口将对话连接到员工智能体。

配置与员工数据位于 `~/.joytrunk`。路径与配置结构见 [agent.md](../agent.md)。

---

## 核心概念

- **负责人** — 你；在本机创建并拥有所有员工。
- **员工** — 具备角色与性格的 AI 智能体。像和真人一样对话，他们会回复并完成任务；可通过网页、`joytrunk chat`、App 或飞书、QQ 等使用。
- **渠道** — 网页、CLI、App 及集成（飞书、QQ、Telegram 等）。无论在哪工作都能触达员工。
- **生存规则** — 员工不得泄露你的主机或敏感信息；仅能以保护隐私的方式协助他人。

---

## 快速开发

从仓库开发时（例如在 `develop` 分支）：

1. 克隆并切分支：`git clone <repo> && cd joytrunk && git checkout develop`
2. **CLI：** 在仓库根目录执行 `cd cli && pip install -e ".[dev]" && joytrunk onboard`。之后按上文使用 `joytrunk`、`joytrunk server`、`joytrunk gateway`、`joytrunk chat`。测试：在 `cli/` 下运行 `pytest -v`。
3. **网页 UI 开发：** 在 `joytrunk server` 已运行的前提下，执行 `cd cli/joytrunk/ui && npm run dev`，在 http://localhost:32893 热更新（API 代理到 32901）。
4. 官网（Vue）与云后端（Node）在独立私有仓库中。产品与架构详见 [agent.md](../agent.md) 与 [product.md](../product.md)。

---

## 架构

各组件关系简述：

- **CLI**（Python）— `onboard`、`chat`、`employee`、`server`、`gateway`、`status`、`memory`、`log`、`docs` 等。配置：`~/.joytrunk/config.json`；每员工目录：`~/.joytrunk/workspace/employees/<id>/`。
- **本地 server**（Node，`joytrunk server`）— 在 32901 提供 Vue 界面与 REST API；仅与 gateway 及本地配置通信。
- **Gateway**（Python，`joytrunk gateway`）— 32900 上的 A2A 服务；在你发送对话时运行员工智能体循环。
- **官方后端**（Node）— 云服务（注册、IM、LLM Router）在独立私有仓库中；部署后用于账号绑定或云能力。

---

## 文档

| 文档 | 说明 |
|------|------|
| [readme/README_zh.md](README_zh.md) | 中文快速上手 |
| [readme/websocket.md](websocket.md) | 官网与 CLI 的 WebSocket 流程：bind、/ws/cli、/ws/im、故障排查 |
| [product.md](../product.md) | 产品定义、负责人–员工模型、流程 |
| [agent.md](../agent.md) | 实现蓝图、路径、配置、路线图 |
| CLI 命令 | 运行 `joytrunk docs` 或 `joytrunk docs --local` 查看完整命令说明。 |

---

## 参与贡献

欢迎贡献。路线图与实现状态见 [agent.md](../agent.md)。

---

<p align="center">
  <sub>JoyTrunk 在本仓库中完成规格与设计。代码库中还包含 nanobot 作为参考；JoyTrunk 为独立产品，运行时不依赖 nanobot。</sub>
</p>
