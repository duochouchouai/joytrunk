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


**JoyTrunk** gives you a full team of AI employees that run entirely on your machine. You're the owner: create employees with different roles and personalities, then chat with them like with real people from the CLI, the local web UI, or the app—and through Feishu, QQ, and other tools you already use, anytime, anywhere. Say what you need and your AI team gets it done: research, writing, coding, day-to-day tasks. Everything stays on your disk unless you choose to connect to cloud services.

- **Local-first.** Config, conversations, and memory live under `~/.joytrunk` (Windows: `%USERPROFILE%\.joytrunk`). Your team, your rules.
- **Multi-employee.** Run several employees at once, each with its own role and style; switch between them in the TUI or web chat.
- **CLI + Web + App.** Use `joytrunk chat` in the terminal, the built-in Vue UI, or the app. Your employees are a message away on Feishu, QQ, and more.
- **Open source.** Install via `pip`; extend and self-host with no vendor lock-in.

**Requirements:** Python 3.11+, Node.js 18+.

---

## Quick start

Follow these steps in order. After step 5 you can open the web UI in a browser or use the CLI to chat.

### 1. Install

```bash
pip install joytrunk
```

Or from this repo:

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

### 3. Build the web UI

Do this once if you want the browser interface; skip it if you only use the CLI.

```bash
cd cli/joytrunk/ui
npm install
npm run build
```

`joytrunk server` will serve this build. Rebuild after pulling UI changes when needed.

### 4. Start the server and the gateway

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

1. Clone and branch: `git clone <repo> && cd joytrunk && git checkout develop`
2. **CLI:** From repo root, `cd cli && pip install -e ".[dev]" && joytrunk onboard`. Use `joytrunk`, `joytrunk server`, `joytrunk gateway`, `joytrunk chat` as above. Tests: `pytest -v` from `cli/`.
3. **Web UI dev:** With `joytrunk server` running, run `cd cli/joytrunk/ui && npm run dev` for hot reload at http://localhost:32893 (proxies API to 32901).
4. `vue/` is the marketing site, `nodejs/` the cloud backend. See [agent.md](agent.md) and [product.md](product.md) for details.

---

## Architecture

How the pieces fit together:

- **CLI** (Python) — `onboard`, `chat`, `employee`, `server`, `gateway`, `status`, `memory`, `log`, `docs`, etc. Config: `~/.joytrunk/config.json`; per-employee dirs under `~/.joytrunk/workspace/employees/<id>/`.
- **Local server** (Node, `joytrunk server`) — Serves the Vue UI and REST API on 32901; talks only to the gateway and local config.
- **Gateway** (Python, `joytrunk gateway`) — A2A on 32900; runs the employee agent loop when you send a chat message.
- **Official backend** (Node, `nodejs/`) — Cloud services (registration, IM, LLM Router), separate from the local server; used for account linking or cloud features.

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

<p align="center">
  <sub>JoyTrunk is specified and designed in this repository. The codebase also contains nanobot as a reference; JoyTrunk is a separate product and does not depend on nanobot at runtime.</sub>
</p>
