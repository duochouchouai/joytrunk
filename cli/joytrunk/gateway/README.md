# A2A Gateway

网页端（聊天记录页、对话页）与 CLI 的「与员工对话」均通过 A2A Gateway 转发到员工智能体。需**同时**运行两个进程：

## 1. 启动后端（Node 管理界面 + API）

```bash
joytrunk server
```

默认端口由配置决定（如 32893），用于提供管理界面和 `/api/employees/:id/chat` 等接口。

## 2. 启动 A2A Gateway（接收网页/CLI 消息并执行员工循环）

**另开一个终端**，执行：

```bash
joytrunk gateway
```

- 默认监听 `127.0.0.1:32900`（端口仅由 **cli/.env** 的 `JOYTRUNK_A2A_PORT` 配置，不读 config.json）。
- 在 cli 目录下复制 `.env.example` 为 `.env` 即可；默认 `JOYTRUNK_A2A_PORT=32900`，无需改即可使用。
- 启动后日志中会看到类似：`A2A Gateway listening on 127.0.0.1:32900`。

## 检查 Gateway 是否可用

```bash
joytrunk gateway status
```

若显示「Gateway 可用」且给出 base URL，说明已就绪；网页端发送消息会由 server 转发到 Gateway，再由 Gateway 调用员工智能体并返回回复。

## 流程简述

1. 浏览器：`POST /api/employees/:id/chat`（发到 joytrunk server）
2. Server：根据 cli/.env 的 `JOYTRUNK_A2A_PORT`（默认 32900）请求 `http://127.0.0.1:32900/a2a/v1/tenants/.../message:send`
3. Gateway：接收 A2A 请求，入队并由 Worker 执行 `run_employee_loop`，完成后将回复通过 A2A 返回给 Server
4. Server：把回复与 usage 返回给浏览器

若未启动 Gateway 就发送消息，会看到提示：**「A2A Gateway 未启动或不可达，请先在另一终端运行：joytrunk gateway」**。
