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

## Install and quick start (planned)

Install from PyPI (when published):

```bash
pip install joytrunk
```

Then:

1. **Initialize** config and workspace:
   ```bash
   joytrunk onboard
   ```
2. **Web management**: Open **http://localhost:32890** to manage employees, team, and settings (start the local service first if required, e.g. `joytrunk gateway` or `joytrunk serve`).
3. **CLI**: Use the `joytrunk` CLI to talk to a chosen employee as one of the channels.

Config and workspace paths are the same on both platforms: **Linux/macOS** use `~/.joytrunk`; **Windows** use `%USERPROFILE%\.joytrunk` (e.g. `$env:USERPROFILE\.joytrunk` in PowerShell).

---

## LLM and billing

- **Default**: Requests go through **JoyTrunk Router** (no API key required); usage is metered and billed.
- **Optional**: Owners can configure their **own LLM** (API key, base URL, model). In that case, requests go directly to the owner's endpoint and are not billed by JoyTrunk.

---

## Architecture (planned)

- **CLI** (Python): `joytrunk` entry point, `joytrunk onboard`, CLI as a channel, optional `joytrunk gateway` / `joytrunk status`.
- **Vue**: Web IM and admin UI (employees, team, settings) served at **http://localhost:32890**.
- **Node.js**: Backend (auth, owner/employee/team CRUD, agent and multi-channel routing).

The CLI is provided by a **pip-installable Python package**; the local web UI and API are started by that package (e.g. bound to port **32890** by default).

---

## Docs

| Document | Description |
|----------|-------------|
| [product.md](product.md) | Product definition (owner–employee model, flows, MVP, survival rules). |
| [agent.md](agent.md)   | Implementation blueprint for agents (cli/vue/nodejs, paths, onboarding, progress). |

---

## Contributing

Contributions are welcome. See [agent.md](agent.md) for the current roadmap and implementation status.

---

<p align="center">
  <sub>JoyTrunk is specified and designed in this repository. The codebase also contains <strong>nanobot</strong>, which served as a reference for design and architecture; JoyTrunk is implemented as a separate product and does not depend on nanobot at runtime.</sub>
</p>
