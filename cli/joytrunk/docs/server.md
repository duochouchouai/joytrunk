# joytrunk server

启动本地常驻服务（CLI 内本地管理后端），绑定 32890，**供网页/Electron 等 UI 使用**。目前 CLI 仅实现 TUI，chat 与 employee 直接读写 config.json，**不依赖 server**，因此 server 仅保留供未来或已有网页/桌面端使用。

## 用法

```bash
joytrunk server [--port PORT]
```

### 选项

| 选项 | 说明 | 默认 |
|------|------|------|
| `--port`, `-p` | 监听端口 | 32890 |

## 说明

- 启动 **CLI 包内的本地管理后端**（Node 服务），监听指定端口（默认 32890）。
- 提供网页管理界面（员工、团队、设置）与 REST API；**员工与负责人数据与 CLI 共用 config.json**，不再使用 store.json。
- 若包内 `joytrunk/server/node_modules` 不存在，首次运行时会自动执行 `npm install --omit=dev`。
- 需要本机已安装 **Node.js**（>=18）并加入 PATH。
- 前台运行；退出终端或 Ctrl+C 后服务停止。

## 示例

```bash
# 默认端口 32890
joytrunk server

# 指定端口
joytrunk server --port 32900
```

## 参见

- [onboard](onboard.md) — 初始化后再启动 server
- [index](index.md) — 命令指南首页
