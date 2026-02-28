# joytrunk employee

查看、新增、设置员工。**所有数据存于 config.json**，不连接 server。

## 用法

```bash
joytrunk employee                    # 进入 TUI 菜单：列出/新建/选人进对话/退出
joytrunk employee list                # 列出所有员工（非交互）
joytrunk employee new                # 新建员工（TUI 输入名称）
joytrunk employee set <员工ID> [选项] # 设置员工属性
```

### employee set 选项

| 选项 | 说明 |
|------|------|
| `--name`, `-n` | 员工名称 |
| `--persona` | 人格描述 |
| `--role` | 职责 |
| `--specialty` | 专长 |

## 说明

- 无子命令时进入**互动菜单**：列出员工、新建员工、选择员工进入对话、退出。
- `list` / `new` / `set` 均读写 `~/.joytrunk/config.json` 的 `employees` 与 `ownerId`。
- 新建员工时会创建 `workspace/employees/<id>/` 并复制包内模板。

## 示例

```bash
joytrunk employee
joytrunk employee list
joytrunk employee new
joytrunk employee set abc-123 --name "新名称" --role "助理"
```

## 参见

- [chat](chat.md) — 与员工对话
- [status](status.md) — 查看员工列表
- [index](index.md) — 命令指南首页
