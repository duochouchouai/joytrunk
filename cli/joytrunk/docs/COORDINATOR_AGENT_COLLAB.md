# 多 Agent 协作：协调员员工配置

官网 IM「多 Agent 协作」由**协调员员工**驱动：任务下发给协调员后，协调员在 loop 中多次调用 `send_message_to_employee` 与指定员工对话，每次工具返回会同步到 IM 会话。

## 协调员员工要求

1. **员工 ID**：默认使用 `coordinator`。官网下发任务时若未传 `coordinator_employee_id`，则使用该默认 ID。你也可使用任意员工 ID，在「开始协作」时由后端/前端传入 `coordinator_employee_id`。
2. **owner_id**：必须在员工 `config.json` 中设置与当前用户一致的 `ownerId`，这样 `create_default_registry(..., owner_id=owner_id)` 会为该员工注册 `send_message_to_employee` 与 `list_team_employees`。
3. **SYSTEM_PROMPT**：约定在「多 Agent 协作」场景下的行为（见下）。

## 创建协调员员工

在 JoyTrunk 工作区中创建 ID 为 `coordinator` 的员工（或你指定的 ID）：

- 在 `~/.joytrunk/workspace/employees/coordinator/` 下创建目录；
- 新建 `config.json`，至少包含：
  - `"id": "coordinator"`
  - `"ownerId": "<你的负责人 ID>"`
  - `"name": "协调员"`（或任意名称）

然后从默认模板复制 `SYSTEM_PROMPT.md`、`HEARTBEAT.md` 等（或通过 JoyTrunk 的「新建员工」流程创建该员工），再在 `SYSTEM_PROMPT.md` 中增加或替换为下面「协调员专用说明」段落。

## 协调员专用说明（可写入 SYSTEM_PROMPT.md）

在 SYSTEM_PROMPT 中增加以下约定（可放在「沟通与风格」或文末独立小节）：

```markdown
## 多 Agent 协作场景

当负责人发起「多 Agent 协作」并给出主题或指令时，你需要：

1. 先调用 **list_team_employees** 获取当前团队员工列表（名称与 ID）。
2. 根据负责人给的主题，**依次**向参与协作的员工发起讨论：使用 **send_message_to_employee(target_employee_id, content)**，其中 `target_employee_id` 填员工 ID 或名称（如「2号员工」），`content` 为你向该员工提出的问题或讨论点。
3. 每次工具返回会得到该员工的回复；你可根据回复继续追问或转向下一名员工。
4. 只向本次参与协作的员工发消息，不要向无关员工或自己发消息；按主题依次讨论，避免无限循环。
```

保存后，该员工即具备协调多 Agent 对话的能力。官网 IM 创建「多 Agent 协作」会话并点击「开始协作」时，会向该协调员下发任务，协调员与各员工的对话会实时写入 IM 并推送到前端。

## 工具说明

- **list_team_employees**：返回同负责人下员工列表，用于获取可用的 `target_employee_id`。
- **send_message_to_employee(target_employee_id, content)**：向指定员工发消息并获取其回复；在官网协作场景下，每次回复会由 Gateway 上报为 `agent_reply` 并写入 IM。

以上工具在 `owner_id` 存在时由默认工具注册表自动注册，无需额外配置。
