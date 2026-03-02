# IM 测试用例模板与示例

每个用例采用「输入 - 操作 - 预期」三部分，便于执行与回归。后端 `im.test.js` 中每个 `it('...')` 可对应一个用例编号（注释中写明 IM-xxx）。

## 模板

```text
用例编号：IM-xxx
标题：xxx
前置：依赖 seed（1:1 会话、群会话、多类型消息等）
输入：
  - 用户/会话/消息状态：xxx
  - 请求参数：method, path, body, headers
操作：
  - 步骤 1：xxx
  - 步骤 2：xxx
预期：
  - HTTP 状态码：xxx
  - response.body（或 response.data）中字段：xxx
  - 数据库状态（可选）：表.字段 = 期望值
```

## 示例：拉消息返回 has_more / latest_msg_id（已实现）

```text
用例编号：IM-100
标题：拉取会话消息返回 items、next_cursor、has_more、latest_msg_id
前置：seed 存在 user1、user2；user1 与 user2 的 1:1 会话已创建并有一条消息
输入：X-Owner-Id: 1；conversation_id = 该会话 id
操作：
  1. GET /api/im/conversations/:id/messages
预期：
  - HTTP 200
  - body.items 为数组
  - body.has_more 为布尔
  - body.latest_msg_id 为当前会话最大消息 id（数字）或 null（无消息时）
  - body.next_cursor 存在（可能为 null）
```

对应自动化：`im.test.js` 中 "returns has_more and latest_msg_id after sending message"。

## 示例：标记已读 + 未读清零（Phase 2）

以下为 **Phase 2** 能力示例（依赖「标记已读」接口与会话列表中的 unread_count）。Phase 1 若尚未实现 PATCH read 与 unread_count，可先跳过或改为「仅验证会话列表与拉消息」的用例。

```text
用例编号：IM-101
标题：进入会话后标记已读，未读数清零
前置：seed 存在 user1–user2 的 1:1 会话，且存在 2 条 user2 发给 user1 的消息
输入：user1 的 token（或 X-Owner-Id: 1）；conversation_id = 该会话 id
操作：
  1. GET /api/im/conversations → 该会话 unread_count = 2
  2. PATCH /api/im/conversations/:id/read，body { last_read_msg_id: 最新消息 id }
  3. GET /api/im/conversations → 该会话 unread_count = 0
预期：
  - 步骤 1 返回 200，body（或 data）中该会话 unread_count 为 2
  - 步骤 2 返回 200
  - 步骤 3 返回 200，该会话 unread_count 为 0
  - user_conversation_status 中该 user1+会话 的 last_read_msg_id 为步骤 2 所传值
```

实现 PATCH read 与列表 unread_count 后，在 `im.test.js` 中新增对应 `it('IM-101: ...')` 并勾选本用例。
