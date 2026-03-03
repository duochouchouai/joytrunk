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

## Getting started

One place to go from install to chatting (CLI or web). Config root: **Linux/macOS** `~/.joytrunk`; **Windows** `%USERPROFILE%\.joytrunk`.

**1. Install** — `pip install joytrunk` or from repo: `cd cli && pip install -e ".[dev]"`

**2. Initialize (once)** — `joytrunk onboard`

**3. Build the web UI (once, if you want the browser)** — `cd cli/joytrunk/ui && npm install && npm run build`. Skip if you only use the CLI.

**4. Run server and gateway (two terminals)** — Both must run for web or CLI chat. Terminal 1: `joytrunk server` (http://localhost:32890, Node.js 18+). Terminal 2: `joytrunk gateway` (127.0.0.1:32891, A2A).

**5. Use the product** — **CLI**: `joytrunk chat` (TUI). **Web**: open http://localhost:32890 (employees, chat, Chat history, Logs, Memory, Settings). Vue dev: `joytrunk server` + `cd cli/joytrunk/ui && npm run dev` → http://localhost:32893.

**中文说明**：见 [readme/README_zh.md](readme/README_zh.md)。

---

## LLM and billing

- **Default**: Requests go through **JoyTrunk Router** (default model **MINIMAX-M2.1**; no API key required); usage is metered and billed.
- **Optional**: Owners can configure their **own LLM** (API key, base URL, model) in the local management UI. In that case, requests go directly to the owner's endpoint and are not billed by JoyTrunk.

---

## Architecture

- **CLI** (Python): Entry point `joytrunk` with commands: `onboard`, **`chat`** (TUI: list/select or add employees, then converse; uses A2A when **gateway** is running), **`employee`** (list/new/set), **`server`** (local backend on port 32890 + serves built-in Vue UI), **`gateway`** (A2A server on 32891, required for web and CLI chat to reach the agent loop), `gateway status`, `status`, `language`, `docs`, **`memory`**, **`log`**. Config: global `~/.joytrunk/config.json`; per-employee `~/.joytrunk/workspace/employees/<id>/config.json`.
- **Vue** (local management UI): Source in `cli/joytrunk/ui`, build output in `cli/joytrunk/server/static`. Served at **http://localhost:32890** by `joytrunk server`. Pages: Home, Chat, Employees (list/create/edit), per-employee **Logs**, **Chat history** (with inline chat input), **Memory** (categories/items), Settings (custom LLM, usage). Talks to the local server only.
- **Node.js** (official backend): Cloud services — user registration, JoyTrunk IM, **LLM Router** (default model MINIMAX-M2.1), billing. Separate from the local 32890 server; used when linking an account or using the Router for LLM.

Local flow: **CLI** + **joytrunk server** (API + Vue) + **joytrunk gateway** (A2A). Web and CLI chat both go through the gateway to run the employee agent loop.

---

## Repository layout

| Directory | Role |
|-----------|------|
| **cli/** | Python package `joytrunk`: CLI entry, `onboard`, `chat` (TUI), `employee`, `server` (Node backend on 32890 + serves Vue from `cli/joytrunk/server/static`), `gateway` (A2A on 32891), `memory`, `log`, `status`, `language`, `docs`. Local UI source: `cli/joytrunk/ui`; build output: `cli/joytrunk/server/static`. Install: `pip install -e ./cli`. |
| **vue/** | **Official website only**: Vue 3 + Vite (product page, docs, pricing, auth). Dev: `npm run dev` (port 32892). Local management UI lives in **cli/joytrunk/ui**, not here. |
| **nodejs/** | Official backend (user registration, IM, LLM Router, billing). `npm install && npm start` (default port 32891). |
| **readme/** | [README_zh.md](readme/README_zh.md) — Chinese quick start. |

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
cd joytrunk
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

- **Run CLI**: `joytrunk`, `joytrunk docs` (open command guide), `joytrunk status`, **`joytrunk chat`** (TUI: list/select or add employee, then converse; **joytrunk gateway** must be running for chat to work), **`joytrunk employee`** (list/new/set), **`joytrunk gateway`** / **`joytrunk gateway status`**, **`joytrunk memory`**, **`joytrunk log`**
- **Run local server** (for web UI): `joytrunk server` (backend on 32890; installs Node deps on first run)
- **Run tests**: `pytest -v` (from `cli/`)

### 2. Local server (32890, or 32893 for UI dev)

The **local management backend** is started by the CLI and serves the **built-in local UI** (source in `cli/joytrunk/ui`, build output in `cli/joytrunk/server/static`):

```bash
joytrunk server
```

- Listens at **http://localhost:32890**. That is the single process: API + static UI.
- Provides REST API and SPA (employees, team, settings, chat, logs, memory). Requires **Node.js** 18+ on PATH.
- **Port 32893 (Vue dev only)**: For frontend hot reload, run `cd cli/joytrunk/ui && npm run dev` in a second terminal (with `joytrunk server` still on 32890). The Vite dev server listens on **http://localhost:32893** and proxies `/api` to 32890. Use 32893 only when developing the local UI; production use is 32890.

### 3. Official website frontend (Vue, optional)

Only when developing or deploying the **official website**:

```bash
cd vue
npm install
npm run dev
```

- Dev server on port **32892**, API proxied to 32891. Start the **nodejs** backend first.
- **vue/** is the marketing site only; the **local management UI** is in **cli/joytrunk/ui** and is served by `joytrunk server`.

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

To run the full stack (CLI, web UI, or Vue dev), follow **Getting started** above.

### Conventions and more

- **Conventions**: [agent.md](agent.md) defines paths, config schema, workspace layout, testing, and PowerShell-first command examples.
- **Product**: [product.md](product.md) defines the product and owner–employee model.
- **Multi-agent**: If multiple people or agents work in parallel, see the agent collaboration section in [agent.md](agent.md) to avoid conflicts.

---

## Docs

| Document | Description |
|----------|-------------|
| [readme/README_zh.md](readme/README_zh.md) | Quick start in Chinese (install, server, gateway, chat, Vue UI, logs). |
| [product.md](product.md) | Product definition (owner–employee model, local UI vs official website, flows, MVP, survival rules, default model MINIMAX-M2.1). |
| [agent.md](agent.md)   | Implementation blueprint (cli/vue/nodejs, dual backend, paths, onboarding, progress). |
| **CLI command guide** | `joytrunk docs` opens the online guide; `joytrunk docs --local` for local. Source: `cli/joytrunk/docs/`. |

---

## Contributing

Contributions are welcome. See [agent.md](agent.md) for the current roadmap and implementation status.

---

<p align="center">
  <sub>JoyTrunk is specified and designed in this repository. The codebase also contains <strong>nanobot</strong>, which served as a reference for design and architecture; JoyTrunk is implemented as a separate product and does not depend on nanobot at runtime.</sub>
</p>
