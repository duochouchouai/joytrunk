# JoyTrunk 本地管理界面

构建产物输出到 `../gateway/static`，由 `joytrunk gateway` 提供。

## 开发（热更新，无需每次 build）

**终端 1**：启动本地 Gateway（仅 API，无需先 build）

```bash
joytrunk gateway
```

**终端 2**：启动 Vite 开发服务器（热更新）

```bash
cd cli/joytrunk/ui
npm run dev
```

浏览器打开 **http://localhost:32893**。前端请求 `/api` 会代理到 `http://localhost:32890`。

- 修改 Vue 代码会自动热更新，无需 `npm run build`。
- 发布或不用 dev 时再执行 `npm run build`，然后直接访问 http://localhost:32890 使用 gateway 自带的静态资源。

## 构建（发布或不用 dev 时）

```bash
npm run build
```

之后 `joytrunk gateway` 会直接提供 `gateway/static` 下的页面，可访问 http://localhost:32890 。
