# JoyTrunk 官方后端（nodejs）

全平台注册用户、JoyTrunk 即时通讯后端、LLM Router、计费与用量。与本地 32890 解耦。

**本地管理后端**（负责人/员工/团队 CRUD、config/workspace、32890 API）已迁移至 **cli 包内**，由 `joytrunk server` 启动。Vue 与 CLI 对接本地 32890 时连接的是 cli 启动的 server。

## 本目录职责（规划）

- 全平台**注册用户**、账号与鉴权
- **JoyTrunk 即时通讯后端**（消息、会话、多端同步）
- **LLM Router**：接收来自本地 server 或客户端的推理请求，返回 completion 与 token；用量与计费落库

当前为占位实现（`GET /api/health`），后续按 agent.md §3.3 实现。

## 命令（PowerShell）

```powershell
npm install
npm start
```

默认端口 32891（与本地 server 32890 区分）。测试：`npm test`。
