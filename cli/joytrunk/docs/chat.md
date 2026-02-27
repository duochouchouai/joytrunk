# joytrunk chat

与指定员工对话（CLI 渠道）。需先启动本地 gateway。

## 用法

```bash
joytrunk chat [员工ID]
```

### 参数

| 参数 | 说明 |
|------|------|
| 员工ID | 可选。不填则从配置默认员工或当前唯一员工选择；多名员工时需指定。 |

## 说明

- 作为「CLI 渠道」与 JoyTrunk 员工进行对话：输入消息后回车发送，员工回复显示在终端。
- 输入 `/exit` 或 `/quit` 退出对话。
- **前置条件**：已执行 `joytrunk onboard`，且已启动 `joytrunk gateway`；已在本地管理界面创建至少一名员工；当前负责人已绑定（首次可在 http://localhost:32890 注册/登录）。

## 示例

```bash
# 与默认或唯一员工对话
joytrunk chat

# 与指定员工对话
joytrunk chat <员工UUID>
```

## 参见

- [gateway](gateway.md) — 需先启动 gateway
- [status](status.md) — 查看员工列表与 ID
- [index](index.md) — 命令指南首页
