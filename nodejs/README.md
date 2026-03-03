# JoyTrunk 官方后端（nodejs）

全平台注册用户、JoyTrunk 即时通讯后端、LLM Router、计费与用量。与本地 32890 解耦。

**本地管理后端**（负责人/员工/团队 CRUD、config/workspace、32890 API）已迁移至 **cli 包内**，由 `joytrunk server` 启动。Vue 与 CLI 对接本地 32890 时连接的是 cli 启动的 server。

## 本目录职责（规划）

- 全平台**注册用户**、账号与鉴权
- **JoyTrunk 即时通讯后端**（消息、会话、多端同步）
- **LLM Router**：接收来自本地 server 或客户端的推理请求，返回 completion 与 token；用量与计费落库

当前为占位实现（`GET /api/health`），后续按 agent.md §3.3 实现。

## 环境要求

- **Node.js** >= 18
- **PostgreSQL**：需本地或远程可用的 PostgreSQL 服务；`pg` 驱动依赖系统 **libpq**：
  - **Windows**：安装 [PostgreSQL](https://www.postgresql.org/download/windows/) 客户端或完整安装后自带 libpq；或使用 vcpkg 安装 libpq
  - **macOS**：`brew install libpq`（若 node 找不到，可设置 `PKG_CONFIG_PATH` 或 `LDFLAGS/CPPFLAGS`）
  - **Linux**：`apt install libpq-dev`（Debian/Ubuntu）或等价包
- **Redis**：验证码存储与节流依赖 Redis；本地 `redis-server` 或 Docker。未配置 `REDIS_URL`/`REDIS_HOST` 时发码与验证码登录将返回 503。

## 配置（.env）

在项目根目录（nodejs 下）创建 `.env` 文件（可复制 `.env.example` 后修改）。数据库配置二选一：

**方式一：完整连接串**

```env
DATABASE_URL=postgres://postgres:123456@localhost:5432/joytrunk
```

**方式二：拆分配置**

```env
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=123456
PG_DATABASE=joytrunk
PG_SSL=false
PG_POOL_MAX=10
```

- **本地开发**：`DATABASE_URL=postgres://postgres:123456@localhost:5432/joytrunk`
- **测试**：`npm test` 会先加载 `.env`，并用同一连接串将库名改为 `joytrunk_test` 连接；若该库不存在会自动创建。也可单独设置 `TEST_DATABASE_URL` 指定测试库连接串。
- **生产（SSL）**：`DATABASE_URL=postgres://user:pass@prod-host:5432/joytrunk?sslmode=require`

**Redis（验证码）**

- `REDIS_URL=redis://localhost:6379` 或拆分为 `REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`。必填，否则发码/验证码登录返回 503。
- `CODE_EXPIRE_SECONDS`（默认 300）、`CODE_THROTTLE_SECONDS`（默认 60）可选。

**阿里云短信（可选）**

- 发真实验证码时在 .env 中配置：`SMS_PROVIDER=aliyun`、`SMS_ACCESS_KEY_ID`、`SMS_ACCESS_KEY_SECRET`、`SMS_SIGN_NAME`、`SMS_TEMPLATE_CODE`。模板需含变量 `code`。未配置或配置不完整时仅控制台打印验证码。

**邮件验证码（可选）**

- `MAIL_HOST`、`MAIL_USER`、`MAIL_PASS`、`MAIL_FROM`、`MAIL_PORT`。未配置时控制台打印验证码。`MAIL_DEV_ACCEPT_ALL=true` 仅在**未配置 MAIL_HOST** 时生效（允许任意验证码登录，仅开发）。

首次启动时会自动建库（若不存在）、建表并执行迁移（加列）。

## 命令（PowerShell）

```powershell
npm install
npm start
```

- **测试**：`npm test`（会加载 `.env`，测试库使用 `joytrunk_test`；**需本地或 CI 起 Redis**，无密码时默认 `REDIS_URL=redis://localhost:6379`，有密码时在 .env 中设 `REDIS_URL` 或 `REDIS_PASSWORD`）。

**测试用户（开发/联调）**

- 执行 `npm run seed` 可写入两名测试用户（幂等，可重复执行）：
  - `test1@test.local` / `test123456`（测试用户A）
  - `test2@test.local` / `test123456`（测试用户B）
- 使用「账号密码登录」接口即可用上述账号登录。

**联调环境（多用户模拟）**

- 自动化测试与联调共用同一套测试库（如 `joytrunk_test`）；`npm test` 前会 TRUNCATE 相关表并执行 seed。
- 联调时请求头可带 **X-Owner-Id**（值为 1、2、3 等）模拟不同用户，无需每次登录换 token。仅当 `NODE_ENV=test` 或 `ALLOW_X_OWNER_ID_FALLBACK=true` 时生效，生产环境关闭。
- 启动时 `seedIfEmpty` 会写入 3 个测试用户（测试用户A/B/C，手机 13800000001/02/03），用于群聊等需 3 人的用例；详见 `tests/IM_TEST_CASES.md`。
