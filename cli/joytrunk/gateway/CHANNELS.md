# Gateway Channel 接口说明（阶段 4）

## 概述

Gateway 将 IM 平台消息转为 A2A/内部 InboundMessage 入队，Worker 执行 `run_employee_loop` 后产出结果；出站时按 `(channel, chat_id)` 路由到对应 **Channel** 实现，由 Channel 将 A2A Message/Part 转为平台格式并发送。

首期仅定义接口与注册方式，不实现具体 IM（飞书、Telegram 等）；实现方需实现 `gateway.channel.Channel` 并在 Gateway 启动时 `register_channel(...)`。

## channel 类型与 chat_id（10.30）

- **channel**：字符串常量，如 `feishu`、`telegram`、`cli`、`web`、`agent`。扩展时新增常量即可，Gateway 不枚举校验，仅作路由与日志用。
- **chat_id**：不透明字符串，无统一格式；由各 Channel 实现约定（如飞书 open_chat_id、Telegram chat_id 数字）。Gateway 按 `(channel, chat_id)` 组合唯一标识一会话端点；同一 chat_id 可在不同 channel 下存在（如 `(cli, "123")` 与 `(web, "123")` 为不同会话）。

## 入站（IM → Gateway）

1. 平台收到用户消息后，调用方将消息转为 **A2A Send Message** 或直接构造 **InboundMessage**（含 `target_employee_id`、`owner_id`、`content`、`session_key`、`channel`、`chat_id`）并入队 MessageBus。
2. 若走 A2A：`POST /a2a/v1/tenants/{owner_id}/employees/{employee_id}/message:send`，body 中 `metadata.channel`、`metadata.chat_id` 指明出站路由；`contextId` 用于多轮会话连续性。

## 出站（Worker → IM）

1. Worker 完成 `run_employee_loop` 后调用 `TaskStore.complete(...)`，边界层或单独出站逻辑从 TaskStore 取 Task，得到 `final_content`、`usage`。
2. 从对应 InboundMessage 或 Task 关联信息中取得 `channel`、`chat_id`。
3. 调用 `get_channel(channel)` 获取已注册的 `Channel` 实现，再调用 `channel.send(chat_id, final_content, metadata={...})`，由实现方将内容转为平台格式并发送（如飞书发消息 API、Telegram sendMessage）。

## 实现步骤

1. 实现 `joytrunk.gateway.channel.Channel` 子类，实现 `channel_type` 与 `send(chat_id, content, metadata)`。
2. 在 Gateway 或应用启动时执行 `register_channel(MyFeishuChannel())` 等。
3. 入站：在收到平台 webhook/回调时，构造 A2A 请求或 InboundMessage 并入队；出站：在 Worker 完成或边界层回调中根据 `channel`/`chat_id` 调用对应 Channel.send。

## 参考

- 方案文档 §6 阶段 4、§10.30、§10.45。
