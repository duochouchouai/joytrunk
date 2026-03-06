# Gateway / A2A 测试说明

按方案测试分层与清单，在 `cli/tests/` 与 `cli/joytrunk/server/tests/` 下实现并自测。

## 一、测试文件与范围

| 文件 | 内容 | 阶段 |
|------|------|------|
| `test_a2a_models.py` | Part/Message/Task、part_to_text、message_to_dict、task_to_dict、AgentCard | 阶段 1 |
| `test_gateway_config_schema.py` | Python DEFAULT_CONFIG gateway 段、migrate_from_legacy 保留 gateway | 阶段 1 |
| `test_gateway_task_store.py` | TaskStore create/get/complete/wait_done、owner_id、blocking 通知 | 阶段 1 |
| `test_gateway_bus.py` | MessageBus FIFO、InboundMessage 入队/出队 | 阶段 1 |
| `test_gateway_a2a_http.py` | 入站解析、非 text Part 报错、404/403/400、Get Task、from_employee_id 校验（需 fastapi） | 阶段 1 |
| `test_a2a_client.py` | get_gateway_base_url、send_message 与 usage 映射、不可用返回 None | 阶段 2 |
| `test_send_message_to_employee_tool.py` | 同 owner 校验、A2A 成功/直连回退（需 sqlmodel 等依赖） | 阶段 3 |
| `test_gateway_channel.py` | Channel 常量、register/get_channel、list_channels | 阶段 4 |
| `server/tests/api.test.js` | configSchema：DEFAULT_CONFIG 与 migrateFromLegacy 含 gateway | 阶段 1 |

## 二、运行方式

**Python（cli 目录下）：**
```bash
cd cli
python -m pytest tests/test_a2a_models.py tests/test_gateway_config_schema.py tests/test_gateway_task_store.py tests/test_gateway_bus.py tests/test_gateway_a2a_http.py tests/test_a2a_client.py tests/test_send_message_to_employee_tool.py tests/test_gateway_channel.py -v
```

- 未安装 `fastapi` 时，`test_gateway_a2a_http.py` 整模块跳过。
- 无法导入 `SendMessageToEmployeeTool`（如缺 sqlmodel）时，`test_send_message_to_employee_tool.py` 内用例跳过。

**Node（server 目录下）：**
```bash
cd cli/joytrunk/server
node --test tests/api.test.js
```

## 三、方案清单勾选（阶段 1）

- [x] gateway 段在 Python/Node schema 与迁移中正确读写
- [x] Send Message（仅 text Part）→ Task（working/completed）且 history 正确
- [x] 非 text Part → 400 / Only text parts supported
- [x] Get Task 返回正确 Task；无权限/不存在 → 404
- [x] from_employee_id 不在同 tenant → 403
- [x] worker_concurrency、blocking、TaskStore、Bus 行为（10.34/10.4/10.5）
- [x] Node configSchema 含 gateway，migrateFromLegacy 保留 gateway

blocking=true 等到完成/超时、Node 兼容转发与前端格式（10.29）需起 Gateway + Node 做集成或 E2E；单元/集成已覆盖解析、权限与 Task/Bus/Store。

## 四、阶段 2–4 与通用

- [x] A2A Client：get_gateway_base_url、send_message 与 reply/usage、不可用返回 None
- [x] send_message_to_employee：同 owner 通过、跨 owner/自己报错、A2A 与直连回退（在可导入环境下）
- [x] Channel 接口与注册
- [x] A2A 错误码与 404/403/400 行为；details 不泄露堆栈（10.39 在实现中遵守）
