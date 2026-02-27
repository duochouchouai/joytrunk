# joytrunk status

查看运行状态、已绑定渠道、当前员工列表等。

## 用法

```bash
joytrunk status
```

## 说明

- 显示 **JoyTrunk 根目录** 与 **本地管理页** URL（默认 http://localhost:32890）。
- 若已初始化且 gateway 可达，显示当前负责人下的**员工列表**（ID 与名称）。
- 若尚未初始化或配置文件不存在，提示先执行 `joytrunk onboard`。
- 若无法连接 gateway，提示先执行 `joytrunk gateway` 启动服务。

## 参见

- [onboard](onboard.md) — 初始化配置与工作区
- [gateway](gateway.md) — 启动本地管理后端
- [index](index.md) — 命令指南首页
