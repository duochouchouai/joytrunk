# joytrunk status

查看运行状态、当前员工列表等。**从 config.json 读取**，无需启动 gateway。

## 用法

```bash
joytrunk status
```

## 说明

- 显示 **JoyTrunk 根目录** 与 **本地管理页** URL（默认 http://localhost:32890）。
- 显示当前负责人下的**员工列表**（ID 与名称），数据来自 `config.json`。
- 若尚未初始化或配置文件不存在，提示先执行 `joytrunk onboard`。

## 参见

- [onboard](onboard.md) — 初始化配置与工作区
- [employee](employee.md) — 查看、新增、设置员工
- [gateway](gateway.md) — 启动本地管理后端（可选）
- [index](index.md) — 命令指南首页
