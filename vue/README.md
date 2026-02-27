# JoyTrunk 官网前端（Vue）

本目录**仅包含 JoyTrunk 官方网站**前端：产品介绍、下载/文档/定价、登录注册（手机验证码）、登录后云端即时通讯等。  

**本地管理界面**已迁入 **CLI 包内**（`cli/joytrunk/ui`），由 `joytrunk gateway` 构建并随 32890 提供，不再由此仓库的 vue/ 构建。

## 开发

```bash
npm install
npm run dev
```

- 开发服务器端口 **32892**，代理 `/api` 到 **http://localhost:32891**（JoyTrunk 官方后端）。请先启动 nodejs 后端：`cd nodejs && npm start`。

## 构建

```bash
npm run build
```

- 产物在 `dist/`，部署到官网域名；通过环境变量 `VITE_API_BASE`、`VITE_DOCS_URL` 等配置 API 与文档链接。

## 环境变量

| 变量 | 说明 |
|------|------|
| `VITE_API_BASE` | 官方后端 API 根地址，空为同源 |
| `VITE_DOCS_URL` | 命令文档链接（如官网文档页） |

构建时使用 `.env.official`（`--mode official`）。

## 测试

```bash
npm run test
```

（Vitest）
