# joytrunk chat

与员工对话（CLI 渠道）。**不连接 server**，从 `config.json` 与 workspace 读取设置。

## 用法

```bash
joytrunk chat [员工ID]
```

### 参数

| 参数 | 说明 |
|------|------|
| 员工ID | 可选。不填则进入 TUI：列出当前员工，**最后一项为「新建员工」**；选择员工后进入对话。 |

### 选项

| 选项 | 说明 |
|------|------|
| `--no-tui` | 使用传统单行输入模式，不启动互动式 TUI（需在有多员工时指定员工 ID 或配置默认员工）。 |

## 说明

- 作为「CLI 渠道」与 JoyTrunk 员工对话：输入消息后回车发送，员工回复显示在终端。
- **前置条件**：已执行 `joytrunk onboard`；员工列表与负责人 ID 存于 `config.json`，无需启动 server 即可选择/新建员工并对话。
- TUI 行为：先检查是否有员工；无员工时仅显示「新建员工」「打开管理页」；有员工时列出所有员工，最后一项为「新建员工」，选择后进入对话。
- 输入 `/exit` 或 `/quit` 退出对话。
- 实际调用大模型时，若使用 JoyTrunk Router，需本机可访问 Router 或配置自有 LLM。

## 示例

```bash
# 进入 TUI：选择员工或新建后对话
joytrunk chat

# 与指定员工对话
joytrunk chat <员工ID>

# 单行模式（需至少一名员工且指定 ID 或默认）
joytrunk chat <员工ID> --no-tui
```

## 参见

- [employee](employee.md) — 查看、新增、设置员工
- [status](status.md) — 查看员工列表与 ID
- [index](index.md) — 命令指南首页
