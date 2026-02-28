<div align="center">
  <h1>JoyTrunk</h1>
  <p><strong>Local 24/7 agent team — you're the owner, they're your employees.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
    <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey" alt="Platform">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

**JoyTrunk** is a local, 24/7 agent team product: you act as the **owner** and manage one or more **employees** (AI agents). You interact with them via instant messaging; they complete tasks and report back. The product targets **Linux and Windows** and is distributed via **pip** as an open-source package.

---

## Key concepts

- **Owner–employee model**: Employees are created by and belong to a single owner; together they form a **JoyTrunk team**. The relationship is binding (no transfer of employees).
- **Multi-employee**: One owner can have multiple employees with different roles, personalities, and skills.
- **Channels**: JoyTrunk's own web IM (Vue) and CLI; optional third-party channels (e.g. Feishu, QQ, Telegram).
- **Employee survival rules**: Employees must not disclose the owner's host or sensitive information to anyone else; they may help others only with privacy-preserving, sanitized information.

---

## Install and quick start

Install from PyPI (when published) or from repo:

```bash
pip install joytrunk
# or from repo: cd cli && pip install -e ".[dev]"
```

Then:

1. **Initialize** config and workspace:
   ```bash
   joytrunk onboard
   ```
2. **Chat with employees** (no server required): Run `joytrunk chat` — TUI lists employees (last option: add new); select one to start a conversation. Employees and owner are stored in **per-employee config** under `~/.joytrunk/workspace/employees/<id>/config.json`; the **global** `~/.joytrunk/config.json` holds only global settings (ownerId, gateway, agents.defaults, channels, providers).
3. **Manage employees**: `joytrunk employee` (TUI), `joytrunk employee list`, `joytrunk employee new`, `joytrunk employee set <id> --name ...`
4. **Optional — Web management**: Start `joytrunk server` and open **http://localhost:32890** to manage employees, team, and settings in the browser.

Paths: **Linux/macOS** use `~/.joytrunk`; **Windows** use `%USERPROFILE%\.joytrunk` (e.g. `$env:USERPROFILE\.joytrunk` in PowerShell).

---

## LLM and billing

- **Default**: Requests go through **JoyTrunk Router** (default model **MINIMAX-M2.1**; no API key required); usage is metered and billed.
- **Optional**: Owners can configure their **own LLM** (API key, base URL, model) in the local management UI. In that case, requests go directly to the owner's endpoint and are not billed by JoyTrunk.

---

## Architecture

- **CLI** (Python): Full local client — `joytrunk` entry point, `joytrunk onboard`, **`joytrunk chat`** (TUI: list/select or add employees from per-employee config; no server required), **`joytrunk employee`** (list/new/set employees), `joytrunk server` (starts the **local management backend** on port 32890 for web/UI), `joytrunk status`, `joytrunk language`, `joytrunk docs`. The CLI reads/writes **global** `config.json` (global settings only) and **per-employee** `workspace/employees/<id>/config.json` (each employee as an independent agent; overrides global).
- **Vue** (local management UI): Web IM and admin (employees, team, settings). Served at **http://localhost:32890** when the **CLI** runs `joytrunk server`; talks to the local server only. Binding a JoyTrunk account uses the **official backend** (nodejs) for IM sync.
- **Node.js** (official backend): Cloud services — user registration, JoyTrunk IM backend, **LLM Router** (default model MINIMAX-M2.1), billing. Separate from the local 32890 server; used when the user links an account or uses Router for LLM.

The **local** stack is self-contained: install the CLI, run `joytrunk onboard` and `joytrunk chat` (no server needed for CLI); optionally run `joytrunk server` and open http://localhost:32890 for the Vue UI.

---

## Repository layout

| Directory | Role |
|-----------|------|
| **cli/** | Python 包 `joytrunk`：CLI 入口、`joytrunk onboard`、**`joytrunk chat`**（TUI 选员工/新建，不依赖 server）、**`joytrunk employee`**（list/new/set）、`joytrunk server`（启动本地后端 + 内嵌管理 UI，端口 32890）、`joytrunk status`、`joytrunk language`、`joytrunk docs`。全局配置在 `config.json`，每位员工独立 `workspace/employees/<id>/config.json`。安装：`pip install -e ./cli`。本地管理界面源码在 cli/joytrunk/ui/，构建产出在 gateway/static/。 |
| **vue/** | **仅官网**：Vue 3 + Vite，产品页、下载/文档/定价、手机验证码登录、云端 IM。开发：`npm run dev`（端口 32892）；构建：`npm run build`。 |
| **nodejs/** | JoyTrunk 官方后端（用户注册、IM、LLM Router、计费）。`npm install && npm start`（默认 32891）。 |

---

## Development (develop branch)

Developers work on the **`develop`** branch. The following steps get you from clone to a running stack and tests.

### Prerequisites

- **Node.js** 18+ (for backend and frontend)
- **Python** 3.11+ (for CLI)
- **Conda** (recommended on Windows; optional on Linux/macOS) for a dedicated CLI env

### Clone and branch

```bash
git clone <repo-url>
cd nanobot
git checkout develop
```

### 1. CLI (joytrunk)

Use a dedicated conda env so the `joytrunk` command and tests run in isolation:

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

- **Run CLI**: `joytrunk`, `joytrunk docs` (open command guide), `joytrunk status`, **`joytrunk chat`** (TUI: list/select or add employee, then converse; no server required), **`joytrunk employee`** (list/new/set)
- **Run local server** (optional, for web UI): `joytrunk server` (starts the built-in backend on 32890; installs Node deps on first run)
- **Run tests**: `pytest -v` (from `cli/`)

### 2. Local server (32890)

The **local management backend** is started by the CLI and serves the **built-in local UI** (source in `cli/joytrunk/ui`, built to `cli/joytrunk/gateway/static`):

```powershell
joytrunk server
```

- 监听 **http://localhost:32890**
- 提供 REST API 与 SPA（员工/团队/设置/对话）。
- Requires **Node.js** 18+ on PATH (the CLI runs the server’s Node process from the package).

### 3. 官网前端（Vue，仅官网）

仅当需要开发或部署**官方网站**时使用：

```bash
cd vue
npm install
npm run dev
```

- 开发端口 **32892**，API 代理到 32891。需先启动 **nodejs** 官方后端。
- **vue/** 仅包含官网；本地管理界面在 **cli/joytrunk/ui**，由 server 提供。

### 4. Official backend (nodejs, optional)

For cloud services (user registration, IM, LLM Router, billing):

```bash
cd nodejs
npm install
npm start
```

- Runs the **official backend** (default port 32891), not the local 32890 server.
- Used when deploying the **official website** or when users link a JoyTrunk account.

### Full stack (local)

1. **CLI only** (no server): `joytrunk onboard` → `joytrunk chat` (TUI lists/creates employees from per-employee config).
2. **With web UI**: 在 **cli** 目录构建本地 UI（可选）：`cd cli/joytrunk/ui && npm install && npm run build`；启动 **joytrunk server**；浏览器打开 **http://localhost:32890**。
3. 用 `joytrunk chat` 与员工对话（可不启动 server）；server 与 CLI 共用同一套 per-employee config。

### Conventions and more

- **Conventions**: [agent.md](agent.md) defines paths, config schema, workspace layout, testing, and PowerShell-first command examples.
- **Product**: [product.md](product.md) defines the product and owner–employee model.
- **Multi-agent**: If multiple people or agents work in parallel, check and update the “Agent 协作标注” section in [agent.md](agent.md) to avoid conflicts.

---

## Docs

| Document | Description |
|----------|-------------|
| [product.md](product.md) | Product definition (owner–employee model, local UI vs official website, flows, MVP, survival rules, default model MINIMAX-M2.1). |
| [agent.md](agent.md)   | Implementation blueprint (cli/vue/nodejs, dual backend, paths, onboarding, progress). |
| **CLI command guide** | `joytrunk docs` 打开官网命令指南；`joytrunk docs --local` 本地查看。源码：`cli/joytrunk/docs/`，官网可单独部署。 |

---

## Contributing

Contributions are welcome. See [agent.md](agent.md) for the current roadmap and implementation status.

---

<p align="center">
  <sub>JoyTrunk is specified and designed in this repository. The codebase also contains <strong>nanobot</strong>, which served as a reference for design and architecture; JoyTrunk is implemented as a separate product and does not depend on nanobot at runtime.</sub>
</p>
