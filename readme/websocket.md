# JoyTrunk 官网–CLI WebSocket 连接：运行与测试说明

本文档说明如何运行并验证「官网注册/登录 → CLI 绑定 → WebSocket 长连 → 消息经官网广播」的完整链路。

---

## 1. 环境准备

### 1.1 所需服务

| 服务 | 说明 | 端口/配置 |
|------|------|-----------|
| PostgreSQL | 官网后端数据库 | 默认 5432，`.env` 中 `DATABASE_URL` 或 `PG_*` |
| Redis | 绑定会话（bind code）存储 | 默认 6379，`.env` 中 `REDIS_URL` 或 `REDIS_HOST` |
| 官网后端 | Node.js（Express + WebSocket） | 默认 `http://localhost:32891` |
| 官网前端 | Vue 3 + Vite | 默认 `http://localhost:32892` |
| CLI | Python joytrunk 包 | 本地，需先 `joytrunk onboard` |

### 1.2 启动命令

```bash
# 终端 1：官网后端（需先 cd nodejs 且 npm install）
cd nodejs
npm start
# 输出：JoyTrunk official backend on http://localhost:32891

# 终端 2：官网前端
cd vue
npm run dev
# 默认：http://localhost:32892

# 终端 3：CLI 本地（若仅测绑定可不启动 gateway）
joytrunk onboard   # 仅首次
joytrunk gateway  # 绑定后需启动，以便连官网 /ws/cli
```

### 1.3 环境变量（可选）

- **官网后端**（`nodejs/.env`）：`DATABASE_URL`、`REDIS_URL`、`PORT`、`OFFICIAL_FRONTEND_URL`（绑定页 base URL，默认 `http://localhost:32892`）。
- **CLI**：`JOYTRUNK_OFFICIAL_URL` 默认 `http://localhost:32891`；可在 `~/.joytrunk/config.json` 的 `official.url` 覆盖。

---

## 2. 阶段一：绑定流程

### 2.1 如何运行

1. 启动官网后端与官网前端（见 1.2）。
2. 在本机执行：
   ```bash
   joytrunk bind
   ```
3. 浏览器会自动打开绑定页（如 `http://localhost:32892/bind?code=xxxxxxxx`）。
4. 若未登录：先登录或注册；登录后会跳回同一绑定页。
5. 在绑定页点击「授权本机 JoyTrunk」。
6. 回到终端：CLI 轮询到 `authorized` 后写入 config 并提示「绑定成功」。

### 2.2 如何测试

- **已绑定**：再次执行 `joytrunk bind` 应提示「本机已绑定…」；可用 `joytrunk bind --force` 强制重新绑定。
- **config**：查看 `~/.joytrunk/config.json`，应存在 `official.api_key` 和 `official.url`。
- **轮询**：用无效 code 请求 `GET /api/cli/bind/poll?code=invalid` 应返回 `{ "status": "pending" }`。
- **手动测 API**：
  ```bash
  curl -s -X POST http://localhost:32891/api/cli/bind/start -H "Content-Type: application/json" -d '{}'
  # 应返回 bind_code、bind_url、expires_in_seconds
  ```

---

## 3. 阶段二：WebSocket 长连

### 3.1 如何运行

1. 确保已完成阶段一（`joytrunk bind` 且 config 中有 `official.api_key`）。
2. 启动官网后端（含 `/ws/cli`）。
3. 在另一终端执行：
   ```bash
   joytrunk gateway
   ```
4. 网关启动后会连官网 WebSocket（`ws://localhost:32891/ws/cli`），发送 `auth` 后应收到 `auth_ok`。

### 3.2 如何测试

- **后端日志**：CLI 连上后，后端控制台可打日志（若已加）或通过「有 CLI 连接」的接口/状态判断。
- **断线重连**：关掉官网后端或断网数秒再恢复，CLI 应自动重连（指数退避）；恢复后日志应有「official_ws connected」类输出。
- **心跳**：CLI 每约 30 秒发 `ping`，后端回 `pong`；超时未收 pong 则 CLI 视为断开并重连。
- **鉴权**：用脚本连 `ws://localhost:32891/ws/cli` 并首帧发 `{"type":"auth","api_key":"invalid"}`，应收到 `auth_error` 或连接被关闭。

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
- 收到 `auth_ok` 后即可接收服务端推送；收到 `type: "joytrunk_reply"` 时可根据 `conversation_id` 更新对应会话的回复。

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
| 绑定失败 / poll 一直 pending | Redis 未起或未配置；code 过期；浏览器未点授权 | 检查 `REDIS_URL`；5 分钟内完成授权；重跑 `joytrunk bind` |
| 绑定页打开后无 code | 前端路由或 base URL 错误 | 确认 `OFFICIAL_FRONTEND_URL` 与打开地址一致；URL 中带 `code=` |
| WebSocket 连不上 / 立刻断 | 官网后端未起；端口或 path 错误；防火墙 | 确认后端已起且 `PORT` 一致；CLI 的 `official.url` 为 `http://...`（ws 会自动替换） |
| 收不到任务 | 会话未标为 JoyTrunk 会话；user_id 与绑定账号不一致 | 创建会话时使用 `peer_uid: "joytrunk"`；确认登录账号与 CLI 绑定账号一致 |
| 收不到 joytrunk_reply | 前端未连 `/ws/im` 或未处理 `joytrunk_reply` | 确认 IM 页建立 `/ws/im` 连接并解析 `type: "joytrunk_reply"` |

---

## 7. 接口与消息格式速查

- **POST /api/cli/bind/start**  
  Body 可选：`{ "device_name": "..." }`  
  响应：`{ "bind_code", "bind_url", "expires_in_seconds" }`

- **GET /api/cli/bind/poll?code=xxx**  
  响应：`{ "status": "pending" }` 或 `{ "status": "authorized", "api_key": "jt_..." }`

- **POST /api/cli/bind/confirm**（需登录）  
  Body：`{ "code": "xxx" }`

- **WebSocket /ws/cli**  
  首帧：`{ "type": "auth", "api_key": "jt_..." }`  
  服务端回：`{ "type": "auth_ok" }`  
  心跳：客户端 `{ "type": "ping", "ts": ... }`，服务端 `{ "type": "pong", "ts": ... }`  
  服务端下发任务：`{ "type": "task", "task_id", "owner_id", "employee_id", "content", "session_key", "conversation_id" }`  
  客户端上报：`{ "type": "task_result", "task_id", "status", "content", "conversation_id", "error?" }`

- **WebSocket /ws/im**  
  首帧：`{ "type": "auth", "token": "<JWT>" }`  
  服务端推送：`{ "type": "joytrunk_reply", "task_id", "status", "content", "conversation_id", "error?" }`

- **创建 JoyTrunk 会话**  
  `POST /api/im/conversations`，Body：`{ "type": "direct", "peer_uid": "joytrunk" }`
