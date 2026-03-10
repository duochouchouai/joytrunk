<div align="center">
  
  <img src="imgs/logo.png" alt="JoyTrunk" width="120" />
  <h1>JoyTrunk</h1>
  
  <p><strong>Your own AI team. Local, private, 24/7.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
    <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey" alt="Platform">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

<a href="readme/README_zh.md">点击查看中文版</a>

> *Chat like with real people. Your AI team gets it done.*
> "像跟真人一样聊天，然后你的AI团队就把事情做完了"  


**JoyTrunk** gives you a full team of AI employees that run entirely on your machine. You're the owner: create employees with different roles and personalities, then chat with them like with real people from the CLI, the local web UI, the **Desktop app**, or the mobile app—and through Feishu, QQ, and other tools you already use, anytime, anywhere. Say what you need and your AI team gets it done: research, writing, coding, day-to-day tasks. Everything stays on your disk unless you choose to connect to cloud services.

- **Local-first.** Config, conversations, and memory live under `~/.joytrunk` (Windows: `%USERPROFILE%\.joytrunk`). Your team, your rules.
- **Multi-employee.** Run several employees at once, each with its own role and style; switch between them in the TUI or web chat.
- **CLI + Web + Desktop + App.** Use `joytrunk chat` in the terminal, the built-in Vue UI, the **Electron Desktop app** (starts server & gateway for you), or the mobile app. Your employees are a message away on Feishu, QQ, and more.
- **Open source.** Install via `pip`; extend and self-host with no vendor lock-in.

**Repo structure:** `cli/` — JoyTrunk CLI and local server/gateway; `ui/` — Electron Desktop app; `app/` — mobile app.

**Requirements:** Python 3.11+, Node.js 18+.

---

## Quick start

You can use JoyTrunk in two main ways:

- **Option A — Desktop app (easiest):** Install the CLI in a virtual environment, then run the Electron Desktop app; it will start `joytrunk server` and `joytrunk gateway` for you. No need to open two terminals.
- **Option B — CLI + browser:** Start server and gateway in two terminals, then open the web UI in a browser or use `joytrunk chat`.

Follow the steps below. After setup you can open the web UI in a browser, use the Desktop app, or use the CLI to chat.

### 1. Install

```bash
pip install joytrunk
```

Or from this repo (for development):

```bash
cd cli
pip install -e ".[dev]"
```

### 2. Initialize

Run once:

```bash
joytrunk onboard
```

This creates your config and workspace under `~/.joytrunk`. Accept the defaults if you like.

### 3. Build the web UI (for Option B or for `joytrunk server`)

Do this once if you want the browser interface or the local server; skip it if you only use the Desktop app or CLI TUI.

```bash
cd cli/joytrunk/ui
npm install
npm run build
```

`joytrunk server` will serve this build. Rebuild after pulling UI changes when needed.

### 4. Start the server and the gateway

**If you use the Desktop app (Option A):**  
Create and activate a virtual environment, install the CLI there (`cd cli && pip install -e ".[dev]"`), then from that same environment run the Desktop app:

```bash
cd ui
npm install
npm start
```

The Desktop app will start `joytrunk server` and `joytrunk gateway` automatically in the background. You do **not** need to run them in separate terminals.

**If you use the CLI + browser (Option B):**  
Use two terminals; both must stay running for chat to work.

**Terminal 1 — local server**

```bash
joytrunk server
```

- Listens at http://localhost:32901. First run may install Node dependencies; wait until it reports listening.

**Terminal 2 — A2A gateway**

```bash
joytrunk gateway
```

Listens on 127.0.0.1:32900. Keep it running while you chat.

Ports are in `cli/.env` as `JOYTRUNK_SERVER_PORT` and `JOYTRUNK_A2A_PORT`.

### 5. Use JoyTrunk

- **Desktop app:** Run `cd ui && npm start` (with joytrunk installed in your active environment). Server and gateway start automatically; use the overlay and main window to manage agents.
- **Web:** Open http://localhost:32901, create an employee, then chat. Your AI team handles the rest.
- **CLI:** Run `joytrunk chat` in a third terminal to pick an employee and talk in the TUI. The gateway must stay running.
- **App:** Chat from your phone and connect to Feishu, QQ, and other platforms so you can reach your team from the tools you already use.

中文说明：[readme/README_zh.md](readme/README_zh.md)

---

## What’s running?

- **`joytrunk server`** — Serves the Vue app and REST API on 32901.
- **`joytrunk gateway`** — Connects chat to the employee agents on 32900.

Config and employees live in `~/.joytrunk`. See [agent.md](agent.md) for paths and schema.

---

## Key concepts

- **Owner** — You; you create and own all employees on this machine.
- **Employees** — AI agents with roles and personalities. Chat with them like with real people; they reply and get the work done via web UI, `joytrunk chat`, the app, or Feishu, QQ, and the like.
- **Channels** — Web UI, CLI, app, and integrations (Feishu, QQ, Telegram, etc.). Your employees are reachable from wherever you work.
- **Survival rules** — Employees must not leak your host or sensitive data; they help others only in a privacy-safe way.

---

## Quick development

If you’re developing from the repo, e.g. on `develop`:

1. Clone and branch: `git clone <repo> && cd nanobot && git checkout develop`
2. **CLI:** From repo root, `cd cli && pip install -e ".[dev]" && joytrunk onboard`. Use `joytrunk`, `joytrunk server`, `joytrunk gateway`, `joytrunk chat` as above. Tests: `pytest -v` from `cli/`.
3. **Desktop app (Electron):** With a venv that has joytrunk installed (`cd cli && pip install -e ".[dev]"`), run `cd ui && npm install && npm start`. The app will spawn `joytrunk server` and `joytrunk gateway` for you; no need to run them in separate terminals.
4. **Web UI dev:** With `joytrunk server` running, run `cd cli/joytrunk/ui && npm run dev` for hot reload at http://localhost:32893 (proxies API to 32901).
5. Official site (Vue) and cloud backend (Node) live in separate private repos. See [agent.md](agent.md) and [product.md](product.md) for product and architecture details.

---

## Architecture

How the pieces fit together:

- **CLI** (Python, `cli/`) — `onboard`, `chat`, `employee`, `server`, `gateway`, `status`, `memory`, `log`, `docs`, etc. Config: `~/.joytrunk/config.json`; per-employee dirs under `~/.joytrunk/workspace/employees/<id>/`.
- **Desktop app** (Electron, `ui/`) — Standalone desktop UI; on launch it starts `joytrunk server` and `joytrunk gateway` in the background so devices can connect without running two terminals.
- **Local server** (Node, `joytrunk server`) — Serves the Vue UI and REST API on 32901; talks only to the gateway and local config.
- **Gateway** (Python, `joytrunk gateway`) — A2A on 32900; runs the employee agent loop when you send a chat message.
- **App** (`app/`) — Mobile app and integrations.
- **Official backend** (Node) — Cloud services (registration, IM, LLM Router) are in a separate private repo; used for account linking or cloud features when deployed.

---

## Docs

| Document | Description |
|----------|-------------|
| [readme/README_zh.md](readme/README_zh.md) | 中文快速上手 |
| [readme/websocket.md](readme/websocket.md) | WebSocket flow between official site and CLI: bind, /ws/cli, /ws/im, troubleshooting |
| [product.md](product.md) | Product definition, owner-employee model, flows |
| [agent.md](agent.md) | Implementation blueprint, paths, config, roadmap |
| CLI commands | Run `joytrunk docs` or `joytrunk docs --local` for the full command guide. |

---

## Contributing

Contributions are welcome. See [agent.md](agent.md) for the roadmap and implementation status.

---

## Acknowledgments

This project was inspired by [nanobot](https://github.com/nanobot). We thank the nanobot team for their open-source work and the ideas that helped shape JoyTrunk.

---

<p align="center">
  <sub>JoyTrunk is specified and designed in this repository. Our project was inspired by nanobot; we thank them for opening their work to the community. JoyTrunk is a separate product and does not depend on nanobot at runtime.</sub>
</p>
