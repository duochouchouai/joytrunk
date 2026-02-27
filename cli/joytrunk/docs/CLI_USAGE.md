# JoyTrunk CLI 使用说明（自测用）

按下面步骤可以在本机完整跑通「员工智能体」：你的意图 + 员工提示词 + 历史 → 大模型 → 执行返回结果（如工具调用）。

---

## 1. 安装与初始化

### 方式 A：从源码运行（当前开发）

```powershell
cd e:\Documents\NKU\duochouchouai\nanobot\cli
conda activate joytrunk
pip install -e ".[dev]"
joytrunk onboard
```

### 方式 B：已发布包

```powershell
pip install joytrunk
joytrunk onboard
```

`onboard` 会创建：

- `~/.joytrunk`（Windows：`%USERPROFILE%\.joytrunk`）
- `config.json`、`workspace`、`workspace/skills`、`workspace/memory`

---

## 2. 启动本地管理后端（必须）

```powershell
joytrunk gateway
```

保持此窗口不关。默认在 **http://localhost:32890** 提供网页管理界面和 API。

- 首次运行如提示安装依赖，在 `joytrunk gateway` 所在目录执行 `npm install`（若需要）。
- 在浏览器打开：**http://localhost:32890**

---

## 3. 创建员工并配置 LLM

员工**必须**使用一个大模型：要么「自有 LLM」，要么「JoyTrunk Router」。

### 选项 A：使用自有 LLM（推荐自测）

1. 在浏览器打开 http://localhost:32890 → 进入 **设置**。
2. 配置 **自有 LLM**：
   - **API Key**：你的 OpenAI / 兼容接口的 Key
   - **Base URL**：例如 `https://api.openai.com/v1` 或其它兼容地址
   - **模型**：如 `gpt-3.5-turbo`、`gpt-4` 等
3. 保存后，该负责人下的员工对话都会用这个 LLM。

### 选项 B：使用 JoyTrunk Router

- 若你们有部署 JoyTrunk 官方后端（Node Router），需要让 **gateway** 能访问到 Router 的 chat 接口。
- 方式一：环境变量  
  ```powershell
  $env:JOYTRUNK_ROUTER_URL = "https://你的Router地址/v1"
  joytrunk gateway
  ```
- 方式二：在 `~/.joytrunk/config.json` 里为 `providers.joytrunk` 配置 `apiBase`（Router 的 base URL）。
- 未配置时，CLI 调用会返回 503，提示配置 Router 或使用自有 LLM。

### 创建员工

1. 在 http://localhost:32890 打开 **员工** 页面。
2. 点击创建员工，填写名称等（可选填人格、职责）。
3. 创建成功后记下 **员工 ID**（或只有一个员工时可不记，chat 会自动选）。

---

## 4. 用 CLI 与员工对话（核心）

```powershell
joytrunk chat
```

若有多名员工：

```powershell
joytrunk chat <员工ID>
```

例如：

```powershell
joytrunk chat
# 或
joytrunk chat abc-123-def
```

**行为说明：**

- 每次输入一句话（如「帮我截图」「读一下 SOUL.md」「列出当前目录」）后回车。
- CLI 会：
  1. 把你的**意图**（当前输入）+ 员工的**提示词**（SOUL/AGENTS/TOOLS/记忆等）+ **历史记录** 拼成完整提示；
  2. 发给大模型（自有 LLM 或 Router）；
  3. 若模型返回 **工具调用**（如 `read_file`、`exec`、`list_dir`），CLI 会在本机**执行**这些工具并把结果再发给模型；
  4. 重复 2–3 直到模型给出最终文字回复；
  5. 把最终回复和 token 用量打印出来。
- 输入 `/exit` 或 `exit` 退出对话。

**自测建议：**

- 输入：「帮我读一下 SOUL.md」→ 应触发 `read_file`，并返回文件内容或总结。
- 输入：「列出当前目录」→ 应触发 `list_dir` 或 `exec`，并返回目录列表。
- 再发一条与上面对话相关的追问 → 应能看出**历史**被带入（上下文连贯）。

---

## 5. 其他常用命令

| 命令 | 作用 |
|------|------|
| `joytrunk status` | 查看 JoyTrunk 根目录、本地管理页地址、当前员工列表 |
| `joytrunk docs` | 在浏览器打开命令指南（默认官网） |
| `joytrunk docs --local` | 用包内文档在本地起一个临时网页看文档 |
| `joytrunk --help` | 列出所有子命令 |

---

## 6. 目录与配置位置（便于自测时查看）

- **根目录**：`%USERPROFILE%\.joytrunk`（Windows）或 `~/.joytrunk`（Linux/macOS）
- **配置文件**：`~/.joytrunk/config.json`
- **某员工工作区**：`~/.joytrunk/workspace/employees/<员工ID>/`
  - 内有 `SOUL.md`、`AGENTS.md`、`TOOLS.md`、`memory/` 等；CLI 会从这里读提示词与记忆。
- **CLI 对话历史**：`~/.joytrunk/workspace/employees/<员工ID>/sessions/cli_direct.json`

---

## 7. 常见问题

- **“尚未绑定负责人”**  
  先打开 http://localhost:32890，在网页里完成一次「登录/注册」或使用默认负责人，使 `config.json` 里有 `ownerId`。

- **“无法连接 gateway”**  
  先执行 `joytrunk gateway` 并保持运行，再执行 `joytrunk chat`。

- **“JoyTrunk Router 未配置”**  
  要么在设置里配置**自有 LLM**，要么配置好 Router 的 `JOYTRUNK_ROUTER_URL` 或 `providers.joytrunk.apiBase` 后再用 chat。

- **想确认是否走了工具执行**  
  对话时若模型调用了工具，CLI 会打印一行 `[工具调用: read_file(...)]` 之类的进度；最终回复会基于工具结果生成。

按上述步骤跑通后，就可以验证：**你的意图 + 员工提示词 + 历史 → 大模型 → 对返回结果执行** 是否符合你的设计预期。
