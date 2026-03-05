# JoyTrunk 官网–CLI WebSocket 连接：运行与测试说明

本文档说明如何运行并验证「官网注册/登录 → CLI 绑定 → WebSocket 长连 → 消息经官网广播」的完整链路。

---

## 1. 环境准备

### 1.1 所需服务

| 服务 | 说明 | 端口/配置 |
|------|------|-----------|
| PostgreSQL | 官网后端数据库 | 默认 5432，`nodejs/.env` 中 `DATABASE_URL` 或 `PG_*` |
| Redis | 绑定会话（bind code）存储 | 默认 6379，`nodejs/.env` 中 `REDIS_URL` 或 `REDIS_HOST` |
| 官网后端 | Node.js（Express + WebSocket） | 默认 `http://localhost:32891` |
| 官网前端 | Vue 3；开发用 Vite 或构建后由后端托管 | 开发：Vite `http://localhost:32892`；生产/单进程：后端 32891 托管 `vue/dist` |
| CLI A2A Gateway | joytrunk gateway（Python，接官网任务、跑 agent） | 默认 `127.0.0.1:32900`（`gateway.a2a_port`），与官网 32891 分离避免冲突 |
| CLI | Python joytrunk 包 | 本地，需先 `joytrunk onboard` |

### 1.2 启动方式（二选一）

**方式 A：后端托管前端（单进程，推荐生产/本地一键）**

1. 构建前端：`cd vue && npm run build`
2. 启动后端：`cd nodejs && npm start`
3. 浏览器访问 `http://localhost:32891`，CLI 执行 `joytrunk bind` 时请求 32891，绑定页也为 32891。

**方式 B：开发时前后端分离**

```bash
# 终端 1：官网后端
cd nodejs && npm start
# 输出：JoyTrunk official backend on http://localhost:32891

# 终端 2：官网前端（Vite，/api、/ws 代理到 32891）
cd vue && npm run dev
# 默认：http://localhost:32892

# 终端 3：CLI（绑定默认 32891；若希望走 Vite 则设 official.url 为 32892）
joytrunk onboard   # 仅首次
joytrunk gateway   # 绑定后需启动，以便连 /ws/cli
```

### 1.3 环境变量（可选）

- **官网后端**（`nodejs/.env`）：`DATABASE_URL`、`REDIS_URL`、`PORT`。`OFFICIAL_FRONTEND_URL` 为绑定页 base URL，默认 `http://localhost:32891`（后端托管时与后端同源）；开发时若用 Vite 可设为 `http://localhost:32892`。
- **CLI**：默认请求 `http://localhost:32891`；可在 `~/.joytrunk/config.json` 的 `official.url` 或环境变量 `JOYTRUNK_OFFICIAL_URL` 覆盖。对 localhost/127.0.0.1 会跳过代理（避免 `HTTP_PROXY` 导致 502）。

### 1.4 CLI 本地配置（~/.joytrunk/config.json）与 MiniMax

官网 IM 发消息给 CLI 时，gateway 会通过 joytrunk server（默认 32890）调用大模型；未配置 JoyTrunk Router 时使用**自有 LLM**（`providers.custom`）。若使用 **MiniMax**，需在 `~/.joytrunk/config.json` 中配置对话模型 ID（MiniMax 不支持 `gpt-3.5-turbo`，需填写其文档中的模型名）。

**示例（MiniMax 文本对话 + 记忆 embedding）：**

```json
{
  "providers": {
    "custom": {
      "apiBase": "https://api.minimaxi.com/v1",
      "apiKey": "你的 MiniMax API Key",
      "model": "abab6.5s-32k"
    }
  },
  "agents": {
    "defaults": {
      "model": "abab6.5s-32k",
      "maxTokens": 2048,
      "temperature": 0.1
    }
  },
  "memory": {
    "embedding": {
      "base_url": "https://api.minimaxi.com/v1",
      "api_key": "你的 MiniMax API Key",
      "embed_model": "embo-01",
      "group_id": "你的 GroupId"
    }
  }
}
```

- **对话模型**：`providers.custom.model` 与 `agents.defaults.model` 建议一致，且为 MiniMax 支持的 ID，如 `abab6.5s-32k`、`abab5.5s` 等（以 MiniMax 开放平台文档为准）。
- **记忆**：使用 MiniMax embedding 时需在 `memory.embedding` 中填 `group_id`（或设置环境变量 `MINIMAX_GROUP_ID`），否则易报 2013。
- 修改 config 后需**重启 joytrunk server**（若在跑），gateway 无需重启。

### 1.5 如何复现本次效果（完整步骤）

按下列顺序执行，即可在官网 IM 中与 JoyTrunk 对话并看到回复（含思考过程折叠展示）。

**前提**：本机已安装 Node.js 18+、Python 3.11+，并已执行 `cd cli && pip install -e ".[dev]" && joytrunk onboard`。PostgreSQL、Redis 已启动并已在 `nodejs/.env` 中配置（或使用默认）。

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 构建官网前端：`cd vue && npm run build` | 生成 `vue/dist` |
| 2 | 启动官网后端（调试模式便于看日志）：`cd nodejs && npm run start:debug` | 控制台输出 `JoyTrunk official backend on http://localhost:32891`，浏览器访问 http://localhost:32891 可打开官网 |
| 3 | 新开终端，绑定 CLI：`joytrunk bind` | 浏览器弹出绑定页，登录后点击「授权本机 JoyTrunk」，终端提示绑定成功；`~/.joytrunk/config.json` 中有 `official.api_key`、`official.url` |
| 4 | 新开终端，启动 Gateway：`joytrunk gateway` | 终端输出连接官网 WebSocket、`auth_ok`、员工同步等；后端控制台出现 `[ws/cli] connection opened`、`[ws/cli] auth_ok user_id= N`、`employees synced count= 1`（或更多） |
| 5 | 浏览器打开 http://localhost:32891/app/im（控制台 / IM 聊天） | 左侧为会话列表，若有「与 JoyTrunk 的对话」则选中；若无则通过「新建会话」创建类型为「与 JoyTrunk 对话」的会话 |
| 6 | 在当前会话输入「你好」并发送 | 消息出现在气泡中；后端控制台出现 `[im] joytrunk message: pushing task ...`、`[pendingCliTasks] pushed task to CLI ...`；Gateway 终端出现任务入队、LLM 调用、`task_id=... completed` 等 |
| 7 | 等待数秒 | 同一会话中收到一条**助手回复**气泡（JoyTrunk 助手）；后端控制台出现 `[ws/cli] task_result received ...`、`[ws/im] broadcastToUser user_id= N sockets= 1`（或大于 0）、`task_result broadcast done` |
| 8 | 若 LLM 返回内容含 `<think>...</think>` 块 | 回复气泡**顶部**出现「展开思考过程 (1)」按钮，默认折叠；点击后展开思考内容，再次点击可收起 |

**复现要点**：

- **必须同时运行**：官网后端（nodejs）、CLI gateway（`joytrunk gateway`）；前端可由后端托管（方式 A）或单独 Vite（方式 B）。
- **必须同一账号**：绑定 CLI 的账号与浏览器登录的官网账号一致，否则收不到该用户的 task 或 joytrunk_reply。
- **IM 页需在发消息前打开**：这样 `/ws/im` 才会在 `loadCurrentUser` 后建立并鉴权，后端 `broadcastToUser` 时 `sockets > 0`，前端才能收到 `joytrunk_reply` 并展示回复。
- **思考过程**：仅当模型返回内容中包含 `<think>...</think>` 时才会出现「展开思考过程」；若模型不返回 think 块，则只显示普通回复气泡。

---

## 2. 阶段一：绑定流程

### 2.1 如何运行

1. 启动官网后端（方式 A 或 B，见 1.2）；若用方式 A，无需单独起前端。
2. 在本机执行：`joytrunk bind`
3. 浏览器会自动打开绑定页（默认 `http://localhost:32891/bind?code=xxx`；若配置了 `OFFICIAL_FRONTEND_URL` 则使用该 URL）。
4. 若未登录：先登录或注册，完成后再跳回 `/bind?code=xxx`。
5. 在绑定页点击「授权本机 JoyTrunk」。
6. 回到终端：CLI 轮询到 `authorized` 后写入 config 并提示「绑定成功」。

### 2.2 如何测试

- **已绑定**：再次执行 `joytrunk bind` 应提示「本机已绑定…」；可用 `joytrunk bind --force` 强制重新绑定。
- **config**：查看 `~/.joytrunk/config.json`，应存在 `official.api_key` 和 `official.url`。
- **轮询**：用无效 code 请求 `GET /api/cli/bind/poll?code=invalid` 应返回 `{ "status": "pending" }`。
- **GET /api/cli/bind/start**：浏览器直接打开会返回 405 与提示「请使用 joytrunk bind」；绑定需用 POST。
- **手动测 POST**（CMD 或 Git Bash）：
  ```bash
  curl -s -X POST http://localhost:32891/api/cli/bind/start -H "Content-Type: application/json" -d "{}"
  ```
  应返回 `bind_code`、`bind_url`、`expires_in_seconds`。

---

## 3. 阶段二：WebSocket 长连

### 3.1 如何运行

1. 确保已完成阶段一（`joytrunk bind` 且 config 中有 `official.api_key`）。
2. 启动官网后端（含 `/ws/cli`）。若需在后端控制台看到 CLI 连接/鉴权/断开日志，请用**调试模式**：
   ```bash
   cd nodejs
   npm run start:debug
   ```
   或设置环境变量后启动：`DEBUG_WS=1 node server.js`（Windows 下可 `set DEBUG_WS=1&& node server.js`）。
3. 在另一终端执行：
   ```bash
   joytrunk gateway
   ```
4. 网关启动后会连官网 WebSocket（`ws://<official.url>/ws/cli`，默认 `ws://localhost:32891/ws/cli`），发送 `auth` 后应收到 `auth_ok`。

### 3.2 如何测试

- **后端日志**：使用 `npm run start:debug` 时，CLI 连上后控制台会打印 `[ws/cli] connection opened`、`[ws/cli] auth_ok user_id= <id>`；断开时打印 `[ws/cli] connection closed user_id=<id>`。未开调试时后端默认不打印这些日志。
- **员工同步**：CLI 鉴权成功后会自动发送当前本机员工列表（`type: "employees"`），后端写入表 `user_cli_employees`；调试模式下会打印 `employees synced count= N`。IM 可通过 **GET /api/cli/employees**（需登录）获取该用户已同步的 CLI 员工列表，用于选择员工并下发带 `employee_id` 的任务。
- **断线重连**：关掉官网后端或断网数秒再恢复，CLI 应自动重连（指数退避）；恢复后 CLI 会再次同步员工列表。
- **心跳**：CLI 每约 30 秒发 `ping`，后端回 `pong`；超时未收 pong 则 CLI 视为断开并重连。
- **鉴权**：用脚本连 `ws://localhost:32891/ws/cli` 并首帧发 `{"type":"auth","api_key":"invalid"}`，应收到 `auth_error` 或连接被关闭；start:debug 下会打印 `auth failed: invalid api_key`。

---

## 4. 阶段三：消息链路

### 4.1 如何运行

1. 官网后端、官网前端、CLI gateway 同时运行（且 CLI 已绑定）。
2. 在官网前端登录后，创建「与 JoyTrunk 的对话」：
   - 调用 `POST /api/im/conversations`，body：`{ "type": "direct", "peer_uid": "joytrunk" }`（或前端提供「与 JoyTrunk 对话」入口）。
3. 在该会话中发送一条消息（如「你好」）。
4. 后端将任务推送给该用户的 CLI（或写入待发队列）；CLI 执行 agent 后通过 WebSocket 上报 `task_result`，后端再向该用户的 IM 连接广播 `joytrunk_reply`。

### 4.2 如何测试

- **CLI 控制台/日志**：发送消息后，运行 gateway 的终端或日志中应出现「收到任务」「enqueued task」等；执行完成后有上报。
- **官网 IM**：若前端已接 `/ws/im` 并处理 `joytrunk_reply`，同一会话中应出现 JoyTrunk 的回复；若开启「云端保留」（见阶段四），刷新后应能看到该条消息历史。
- **CLI 离线**：停止 gateway 后发消息，再启动 gateway；应能拉取到待发任务并执行，然后上报结果。

### 4.3 IM WebSocket（/ws/im）

- 前端连接 `ws://localhost:32891/ws/im`，首帧发送：`{ "type": "auth", "token": "<JWT>" }`（与登录态一致）。
- **鉴权**：`token` 可为 JWT，或开发环境下为数字用户 ID 字符串（后端 `ALLOW_X_OWNER_ID_FALLBACK` 时接受）。IM 页会在 `loadCurrentUser` 后再建立连接，无 JWT 时可用当前用户 ID 作为 token，以便后端将连接登记到对应用户，从而收到 `joytrunk_reply` 推送。
- 收到 `auth_ok` 后即可接收服务端推送；收到 `type: "joytrunk_reply"` 时可根据 `conversation_id` 更新对应会话的回复。
- **回复展示**：若 LLM 返回内容中包含 `<think>...</think>` 块（如 DeepSeek-R1 等思考模型），前端会将其折叠为「展开思考过程」按钮，默认不显示，点击后可展开/收起。
- **故障**：若后端日志出现 `broadcastToUser user_id= N sockets= 0`，说明该用户没有已鉴权的 `/ws/im` 连接；请确认 IM 页已打开且已完成 auth（JWT 或数字 ID），或检查前端是否在 `loadCurrentUser` 之后再调用 `connectImWs`。

---

## 5. 阶段四：可选保留数据（sync_joytrunk_chat）

### 5.1 如何运行

- 在官网「个人设置」中勾选/取消「在云端保留与 JoyTrunk 的对话记录」；对应接口为 `PATCH /api/users/me`，body：`{ "sync_joytrunk_chat": true }` 或 `false`。
- 关闭保留后，在「与 JoyTrunk 的对话」中发消息并收到回复；再开启保留后重复一次。

### 5.2 如何测试

- **关闭保留**：`sync_joytrunk_chat = false` 时，CLI 上报的 agent 回复**不会**写入 `messages` 表；仅通过 `/ws/im` 实时推送。可查 DB 该会话的 `messages` 表，不应出现 JoyTrunk 账号新插入的回复行（或仅旧数据）。
- **开启保留**：`sync_joytrunk_chat = true` 时，agent 回复会写入 `messages`，刷新会话历史应能看到。

---

## 6. 故障排查

| 现象 | 可能原因 | 建议 |
|------|----------|------|
| **502 Bad Gateway** | 后端未启动；或 CLI 经代理访问本地导致 502 | 启动 nodejs（`npm start`）；CLI 对 localhost 已跳过代理，若仍 502 可检查是否曾设 `official.url` 为 32892 且未起 Vite，改为 32891 或删该字段；用 `curl -X POST http://127.0.0.1:32891/api/cli/bind/start -H "Content-Type: application/json" -d "{}"` 自测 |
| 绑定失败 / poll 一直 pending | Redis 未起或未配置；code 过期；浏览器未点授权 | 检查 `REDIS_URL`/`REDIS_HOST`；5 分钟内完成授权；重跑 `joytrunk bind` |
| 绑定页打开后端口错 | 后端生成的 bind_url 用了错误的前端 base | 确认 `OFFICIAL_FRONTEND_URL`（默认 32891）；后端托管前端时不要设为 32892 |
| WebSocket 连不上 / 立刻断 | 后端未起；端口或 path 错误；防火墙 | 确认后端已起；CLI 的 `official.url` 与后端一致（ws 由 http 自动替换） |
| 收不到任务 | 会话未标为 JoyTrunk；user_id 与绑定账号不一致 | 创建会话时 `peer_uid: "joytrunk"`；登录账号与 CLI 绑定账号一致 |
| 收不到 joytrunk_reply | 前端未连 `/ws/im` 或未处理 `joytrunk_reply`；或该用户无已鉴权 IM 连接（sockets=0） | 确认 IM 页建立 `/ws/im` 并解析 `type: "joytrunk_reply"`；auth 使用 JWT 或（开发环境）数字用户 ID；IM 页在 loadCurrentUser 后再 connectImWs |
| Gateway 不向官网回传 task_result | 官方 WS 客户端误判连接已关闭（如依赖不存在的 `ws.closed`） | Gateway 使用 `official_ws_client.send_task_result` 时仅判断 `_ws is not None` 并 try/except 发送；websockets 库无 `closed` 属性 |

---

## 7. 接口与消息格式速查

- **POST /api/cli/bind/start**  
  Body 可选：`{ "device_name": "..." }`  
  响应：`{ "bind_code", "bind_url", "expires_in_seconds" }`  
  GET 同一 URL 返回 405，提示使用 `joytrunk bind`。

- **GET /api/cli/bind/poll?code=xxx**  
  响应：`{ "status": "pending" }` 或 `{ "status": "authorized", "api_key": "jt_..." }`

- **POST /api/cli/bind/confirm**（需登录）  
  Body：`{ "code": "xxx" }`

- **WebSocket /ws/cli**  
  首帧：`{ "type": "auth", "api_key": "jt_..." }`  
  服务端回：`{ "type": "auth_ok" }`  
  客户端同步员工（鉴权成功后发送）：`{ "type": "employees", "employees": [ { "id": "<employee_id>", "name": "..." } ] }`，后端写入 `user_cli_employees` 表，供 IM 通过 GET /api/cli/employees 获取。  
  心跳：客户端 `{ "type": "ping", "ts": ... }`，服务端 `{ "type": "pong", "ts": ... }`  
  服务端下发任务：`{ "type": "task", "task_id", "owner_id", "employee_id", "content", "session_key", "conversation_id" }`  
  客户端上报：`{ "type": "task_result", "task_id", "status", "content", "conversation_id", "error?" }`

- **GET /api/cli/employees**（需登录）  
  响应：`{ "employees": [ { "id": "<employee_id>", "name": "..." } ] }`，为当前用户已同步的 CLI 员工列表；IM 发消息时可选择员工并将 `employee_id` 带入任务 payload。

- **WebSocket /ws/im**  
  首帧：`{ "type": "auth", "token": "<JWT>" }`  
  服务端推送：`{ "type": "joytrunk_reply", "task_id", "status", "content", "conversation_id", "error?" }`

- **创建 JoyTrunk 会话**  
  `POST /api/im/conversations`，Body：`{ "type": "direct", "peer_uid": "joytrunk" }`
