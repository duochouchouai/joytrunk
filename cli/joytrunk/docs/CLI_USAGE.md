# JoyTrunk CLI 使用说明（自测用）

按下面步骤可以在本机完整跑通「员工智能体」：你的意图 + 员工提示词 + 历史 → 大模型 → 执行返回结果（如工具调用）。

**约定**：**所有配置均在 `config.json`**（`~/.joytrunk/config.json`），包括员工列表与负责人 ID；**不再使用 store.json**。chat、employee、status 均直接读写 config.json，**无需先启动 gateway**。

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

## 2. 创建员工并与员工对话（无需 gateway）

```powershell
joytrunk chat
```

- 若无员工，TUI 会提示「新建员工」或「打开管理页」；选择新建后输入名称即创建并进入对话。
- 若有员工，TUI 列出所有员工，**最后一项为「新建员工」**，选择后进入对话或新建。
- 或使用 `joytrunk employee new` 新建、`joytrunk employee list` 查看列表、`joytrunk employee set <id> --name ...` 设置属性。

**可选**：若需网页管理界面或 Electron 等 UI，再执行 `joytrunk gateway` 并保持运行；gateway 与 CLI 共用同一 config.json。

---

## 3. 配置 LLM

员工**必须**使用一个大模型：要么「自有 LLM」，要么「JoyTrunk Router」。

### 选项 A：使用自有 LLM（推荐自测）

1. 启动 `joytrunk gateway` 后，在浏览器打开 http://localhost:32890 → 进入 **设置**；或直接编辑 `~/.joytrunk/config.json` 的 `providers.custom`。
2. 配置 **自有 LLM**：API Key、Base URL、模型名等，保存。

### 选项 B：使用 JoyTrunk Router

- 环境变量 `$env:JOYTRUNK_ROUTER_URL = "https://你的Router地址/v1"` 或 config 中 `providers.joytrunk.apiBase`。
- 未配置时，对话会返回 503，提示配置 Router 或使用自有 LLM。

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
| `joytrunk status` | 查看根目录、本地管理页地址、当前员工列表（从 config.json 读取） |
| `joytrunk employee` | 员工管理 TUI：列出/新建/选人进对话 |
| `joytrunk employee list` | 列出员工 |
| `joytrunk employee new` | 新建员工 |
| `joytrunk employee set <id> --name ...` | 设置员工属性 |
| `joytrunk docs` | 在浏览器打开命令指南（默认官网） |
| `joytrunk docs --local` | 用包内文档在本地起一个临时网页看文档 |

---

## 6. 目录与配置位置

- **根目录**：`%USERPROFILE%\.joytrunk`（Windows）或 `~/.joytrunk`（Linux/macOS）
- **配置文件**：`~/.joytrunk/config.json`（**含员工列表、ownerId**，无 store.json）
- **某员工工作区**：`~/.joytrunk/workspace/employees/<员工ID>/`
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
