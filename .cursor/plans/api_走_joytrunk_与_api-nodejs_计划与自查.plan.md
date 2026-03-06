---
name: API 走 JoyTrunk + 后端改为 /api-nodejs（计划与自查）
overview: 所有 API 请求统一经 JoyTrunk 入口；Node 官方后端路由前缀改为 /api-nodejs；Vue 开发通过 Vite 双代理分流 /api → 32890、/api-nodejs → 32893。本文档含实施步骤与自查补充项。
todos: []
isProject: false
---

# API 走 JoyTrunk + 后端 /api-nodejs 方案与自查

## 目标

- **前端**：所有请求先到同一入口（开发时为 Vite 32892，生产为官网/网关），再按路径分流。
- **Node 后端**：路由前缀由 `/api` 改为 `**/api-nodejs`**，与 JoyTrunk 提供的 `/api` 区分。
- **开发代理**：`/api` → 32890（JoyTrunk），`/api-nodejs` → 32893（Node）；需同时启动两个服务。

---

## 一、实施步骤

### 1. Vite 代理（[vue/vite.config.js](vue/vite.config.js)）

- 增加 `/api-nodejs` 代理到 `http://localhost:32893`，**且写在 `/api` 之前**（更具体前缀优先）。
- 保留 `/api` 代理到 `http://localhost:32890`。
- 不重写 path，仅按前缀转发。

```js
proxy: {
  '/api-nodejs': { target: 'http://localhost:32893', changeOrigin: true },
  '/api':       { target: 'http://localhost:32890', changeOrigin: true },
}
```

### 2. Node 后端前缀

- [nodejs/server.js](nodejs/server.js)：`/api/health` → `/api-nodejs/health`；`/api/auth` → `/api-nodejs/auth`；`/api/users`、`/api/im`、`/api/employees` → `/api-nodejs/users`、`/api-nodejs/im`、`/api-nodejs/employees`；`/api/teams/current` → `/api-nodejs/teams/current`。
- [nodejs/wsGateway.js](nodejs/wsGateway.js)：`app.ws('/api/gateway/ws', ...)` → `app.ws('/api-nodejs/gateway/ws', ...)`；文件顶部注释改为「`/api-nodejs/gateway/ws`」。
- [nodejs/routes/employees.js](nodejs/routes/employees.js)：顶部注释改为「GET/POST /api-nodejs/employees, ...」。

### 3. Vue api.js（[vue/src/api.js](vue/src/api.js)）

- **走 Node（改为 `/api-nodejs/...`）**：auth 中除 register/login 外（sendCode、loginByCode、sendEmailCode、loginByEmailCode、loginByPassword）；users.me、updatePassword、deactivate；employees 的 list/create/get/update/delete；teams.current；im 全部。
- **走 JoyTrunk（保留 `/api`）**：auth.register、auth.login；owners.me；config、usage、configPatch、configClear；employees.logs、employees.chat。
- **401 排除**：在 `request()` 内 401 处理中，增加对 `path.startsWith('/api-nodejs/auth/')` 的排除，避免登录/验证码等未带 token 时被清 token 并跳转登录。
- **可选**：定义常量如 `API_NODEJS = '/api-nodejs'`、`API = '/api'`，请求路径用常量拼接，减少硬编码与漏改。

### 4. 测试路径（nodejs/tests）

- [nodejs/tests/api.test.js](nodejs/tests/api.test.js)：`/api/health` → `/api-nodejs/health`。
- [nodejs/tests/im.test.js](nodejs/tests/im.test.js)：所有 `/api/health`、`/api/auth/...`、`/api/users/...`、`/api/im/...` → `/api-nodejs/...`。
- [nodejs/tests/gateway-ws.test.js](nodejs/tests/gateway-ws.test.js)：WebSocket URL `ws://.../api/gateway/ws` → `ws://.../api-nodejs/gateway/ws`；其中 HTTP 请求路径 `/api/users/me`、`/api/auth/...` 等 → `/api-nodejs/...`。

### 5. 文档

- [vue/README.md](vue/README.md)：开发说明改为「端口 32892；`/api` 代理到 **32890**（JoyTrunk），`/api-nodejs` 代理到 **32893**（Node）；需同时启动 JoyTrunk server 与 nodejs」。
- 根 [README.md](README.md)：第 138 行附近「开发端口 32892，API 代理到 32893」改为上述双代理与双服务说明。
- **开发时 VITE_API_BASE**：开发环境**不要设置** `VITE_API_BASE`（或设为空），让请求走 Vite 同源，由代理分流；否则请求会直连单一端口，导致另一半接口 404。在 README 与 .env 示例中说明。
- **生产**：若使用 `VITE_API_BASE` 为 API 域名，则该域名（或网关）必须同时提供 `/api` 与 `/api-nodejs` 的反向代理，分别指向 JoyTrunk 与 Node；并配置 WebSocket 的 `Upgrade`/`Connection` 到 `/api-nodejs/gateway/ws`。

---

## 二、路由与路径归属清单

### Node 路由（改前缀后）


| 路径                                               | 说明                                                                                                        |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| GET /api-nodejs/health                           | 健康检查                                                                                                      |
| /api-nodejs/auth/*                               | send-code, send-email-code, login-by-code, login-by-email-code, login-by-password（**无** register / login） |
| /api-nodejs/users/*                              | me, me/password, me/deactivate                                                                            |
| /api-nodejs/im/*                                 | conversations, messages 等                                                                                 |
| /api-nodejs/employees, /api-nodejs/employees/:id | CRUD + 补偿 DELETE                                                                                          |
| GET /api-nodejs/teams/current                    | 当前用户与 agents                                                                                              |
| WS /api-nodejs/gateway/ws                        | Gateway WebSocket                                                                                         |


### Vue 请求归属


| api 方法                                                                       | 前缀          | 说明                     |
| ---------------------------------------------------------------------------- | ----------- | ---------------------- |
| auth.register, auth.login                                                    | /api        | JoyTrunk 提供，Node 无此二路由 |
| auth.sendCode, loginByCode, sendEmailCode, loginByEmailCode, loginByPassword | /api-nodejs | Node                   |
| owners.me                                                                    | /api        | JoyTrunk               |
| users.me, updatePassword, deactivate                                         | /api-nodejs | Node                   |
| employees.list, create, get, update, delete                                  | /api-nodejs | Node                   |
| employees.logs, employees.chat                                               | /api        | JoyTrunk               |
| teams.current                                                                | /api-nodejs | Node                   |
| config, usage, configPatch, configClear                                      | /api        | JoyTrunk               |
| im.*                                                                         | /api-nodejs | Node                   |


---

## 三、自查与补充（实施前必对）

### 3.1 auth.register / auth.login

- **结论**：Node 仅有 send-code、login-by-code 等，**没有** register 和 login 路由。
- **计划要求**：`api.auth.register`、`api.auth.login` 必须继续使用 `**/api`**（JoyTrunk）；仅其余 auth 改为 `/api-nodejs`。

### 3.2 开发环境 VITE_API_BASE

- **结论**：[vue/.env.official](vue/.env.official) 中若写 `VITE_API_BASE=http://localhost:32893`，改前缀后 Node 只提供 `/api-nodejs`，直连 32893 时 `/api` 会 404。
- **计划要求**：开发时**不设** `VITE_API_BASE`（或为空），请求走 Vite 同源（32892），由 Vite 代理分流；在 README 与 .env 示例中写明。

### 3.3 vue/README 与根 README

- **结论**：当前 vue/README 写「代理 `/api` 到 32893」——32893 为 Node，表述错误；且未说明双代理与双服务。
- **计划要求**：见「一、实施步骤」第 5 条；根 README 第 138 行附近同步改为双代理说明。

### 3.4 测试文件全量

- **结论**：避免漏改导致测试仍请求旧路径。
- **计划要求**：api.test.js、im.test.js、gateway-ws.test.js 中所有 `/api/...` 与 `ws://.../api/gateway/ws` 改为 `/api-nodejs/...` 与 `ws://.../api-nodejs/gateway/ws`。

### 3.5 路由与注释

- **结论**：改前缀后注释若仍写 `/api/...` 易误导后续维护。
- **计划要求**：nodejs/server.js、wsGateway.js、routes/employees.js 中涉及路径的注释与文档字符串一律改为 `/api-nodejs/...`。

### 3.6 生产 Nginx / 网关

- **结论**：生产若设 `VITE_API_BASE` 为同一域名或 API 网关，该入口必须同时提供 `/api` 与 `/api-nodejs` 的反向代理。
- **计划要求**：文档或运维说明中补充「生产 Nginx 配置示例」：`/api` 反向代理到 JoyTrunk；`/api-nodejs` 及 `/api-nodejs/gateway/ws`（WebSocket）反向代理到 Node，并保留 `Upgrade`、`Connection` 头。

### 3.7 其他已确认无问题项

- **Node 内部自调用**：未发现 nodejs 内对自身 `/api/` 的 fetch/axios，无需改。
- **api.owners.me**：Vue 中无调用方，保留 `/api` 即可。
- **cli/joytrunk/ui**：独立 Vite（端口 32893），仅代理 `/api` → 32890，不接 Node；**不参与本次改造**，仅改官网 vue/。

---

## 四、验收要点

- 开发时未设置 VITE_API_BASE，npm run dev 后请求 32892，/api/* 到 32890，/api-nodejs/* 到 32893。
- 登录/验证码（sendCode、loginByCode 等）正常；register/login 仍走 /api。
- GET /api-nodejs/employees、POST /api-nodejs/employees、GET /api-nodejs/teams/current、WebSocket /api-nodejs/gateway/ws 均可用。
- nodejs 单元/集成测试全部使用 /api-nodejs 路径并通过。
- vue/README 与根 README 中端口与代理描述正确，并说明需同时启动 JoyTrunk 与 Node。

