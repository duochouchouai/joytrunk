---
name: 记忆处理 run_log 事件
overview: 在 loop 与 context 中为「检索」与「记忆写入」增加结构化 run_log，使 agent.jsonl 中能看到 retrieve 结果与 memorize 是否执行及结果。记忆始终启用；当无 embed/llm 时无法检索或写入，通过 run_log 的 skipped reason 区分。
todos: []
isProject: false
---

# 记忆处理 run_log 事件

## 现状

- **记忆已接入且始终启用**：[loop.py](cli/joytrunk/agent/loop.py) 始终调用 `_memory_clients`，在 `(embed_client or llm_chat_fn)` 时走 `build_messages_with_memory`（内部调 retrieve），并在 `append_turn_done` 后根据 `auto_extract and (embed_client or llm_chat_fn)` 调用 `run_memorize`。
- **日志缺口**：仅在 memorize **抛异常**时写入 `memory_memorize_error`；**没有**以下日志：
  - 是否因无 embed/llm 而跳过带记忆的 message 构建；
  - retrieve 是否执行、返回了多少条 items/categories；
  - memorize 是否执行、成功时写入了多少条、或未提取到条目而跳过。

因此从 agent.jsonl 无法区分：是「无 embed/llm 未走 retrieve」、还是「走了 retrieve 但为空 / memorize 未提取到内容」。

---

## 方案

在现有 [run_log](cli/joytrunk/agent/run_log.py) 上增加两类事件（不修改 run_log 的写入逻辑，只增加 event 类型与 payload 约定），在 [loop.py](cli/joytrunk/agent/loop.py) 和 [context.py](cli/joytrunk/agent/context.py) 中打点。

### 1. 新增事件常量（run_log.py）

- `EVENT_MEMORY_RETRIEVE = "memory_retrieve"`  
  - 含义：本轮 build system prompt 时执行了 retrieve。  
  - payload 建议：`method`（rag/llm）、`query_preview`（当前用户输入截断）、`items_count`、`categories_count`（可选 `resource_count`），便于确认「有检索且返回条数」。
- `EVENT_MEMORY_MEMORIZE = "memory_memorize"`  
  - 含义：本轮 append_turn 后执行了 run_memorize 且**未抛异常**。  
  - payload 建议：`items_count`、`resource_id`（若有）、或 `skipped: true` 表示 run_memorize 返回 None（未提取到条目）。
- 保留现有 `memory_memorize_error`，仅在 memorize 抛错时写入（已有）。

### 2. loop.py 打点

- **loop_start 的 payload**：可增加 `memory_has_embed: bool(embed_client)`、`memory_has_llm: bool(llm_chat_fn)`，便于一眼看出本轮是否具备记忆能力。不再包含 `memory_enabled`（记忆始终启用）。
- **在 append_turn_done 之后、调用 run_memorize 时**：  
  - 若**未**执行 memorize（条件不满足）：打一条 `memory_memorize`，payload 如 `{"skipped": true, "reason": "auto_extract_off" | "no_embed_or_llm" | "no_items_extracted"}`，便于区分「未执行」与「执行了但提取为 0」。  
  - 若**执行**了 run_memorize：  
    - 成功且返回非 None：打 `EVENT_MEMORY_MEMORIZE`，payload 含 `items_count`、`resource_id`（若有）；  
    - 成功但返回 None（未提取到条目）：打 `EVENT_MEMORY_MEMORIZE`，payload 含 `items_count: 0` 或 `skipped: true, reason: "no_items_extracted"`；  
    - 抛错：保持现有 `memory_memorize_error`。

### 3. context.py 打点（retrieve）

- **在 build_system_prompt_with_retrieve 内**：在调用 `retrieve(...)` 并得到 `result` 后，需要把「本 run 的 run_id」和「employee_id」传到 context 才能写入 agent.jsonl。  
  - 可选方案 A：在 `build_system_prompt_with_retrieve` 增加可选参数 `run_id: str | None = None` 和 `run_log_fn`（或直接依赖 `from joytrunk.agent.run_log import log as run_log`），在 retrieve 返回后、return 前打 `EVENT_MEMORY_RETRIEVE`，payload 含 `method`、`query_preview`、`items_count`、`categories_count`。  
  - 可选方案 B：在 loop 里调用 `build_messages_with_memory` 之后，再根据条件自己调一次 retrieve（与 context 内逻辑重复），仅用于打 log，不推荐。
- **推荐方案 A**：context 内 retrieve 后打 log，run_id 由 loop 传入（build_messages_with_memory 需增加可选参数 run_id，并传给 build_system_prompt_with_retrieve）。这样单次 retrieve 只执行一次，且日志与「实际注入 system 的检索结果」一致。

### 4. 日志顺序与 run_id

- 所有 memory 相关事件与同轮 loop 使用同一 `run_id`，便于前端按 run 过滤。  
- 顺序：`loop_start` → … → `llm_request`（此时 system 已含 retrieve 结果）→ … → `append_turn_done` → `memory_memorize`（或 `memory_memorize_error`）。  
- 若在 context 内打 retrieve 日志，则 **memory_retrieve** 会在 **llm_request** 之前（因为 build_messages_with_memory 先执行 retrieve 再拼 system，再返回 messages，loop 再打 llm_request）。

---

## 实现要点汇总

| 位置                                          | 变更                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [run_log.py](cli/joytrunk/agent/run_log.py) | 新增常量 `EVENT_MEMORY_RETRIEVE`、`EVENT_MEMORY_MEMORIZE`；在 docstring 中约定 payload 字段；导出新常量。                                                                                                                                                                                                                              |
| [loop.py](cli/joytrunk/agent/loop.py)       | loop_start 的 payload 可增加 `memory_has_embed`、`memory_has_llm`（不包含 memory_enabled）；调用 `build_messages_with_memory` 时传入 `run_id`；在 run_memorize 分支：成功时打 `EVENT_MEMORY_MEMORIZE`（含 items_count 或 skipped + reason），未执行时打 `EVENT_MEMORY_MEMORIZE` 且 payload 为 skipped + reason（仅 `auto_extract_off`、`no_embed_or_llm`、`no_items_extracted`）；保留 memorize 异常时的 `memory_memorize_error`。 |
| [context.py](cli/joytrunk/agent/context.py) | `build_messages_with_memory` 增加可选参数 `run_id`；`build_system_prompt_with_retrieve` 增加可选参数 `run_id`，在 retrieve 返回后若 `run_id` 存在则打 `EVENT_MEMORY_RETRIEVE`（payload：method, query_preview, items_count, categories_count）。**另**：在「长期记忆」段落前插入记忆机制说明（常量 `MEMORY_SYSTEM_INSTRUCTION`），说明检索来源、自动提取、以及 save_memory/search_memory 工具。 |

---

## 验收

- 配置正常且有 embed 或 llm 时，一轮对话的 agent.jsonl 中应出现：`memory_retrieve`（items_count/categories_count 符合预期）、`memory_memorize`（items_count 或 skipped）。  
- 无 embed 且无 llm 时，应出现 `memory_memorize` 且 `skipped: true, reason: "no_embed_or_llm"` 或类似，且无 `memory_retrieve`（因未走 build_system_prompt_with_retrieve）。  
- memorize 抛错时仍只有 `memory_memorize_error`，行为不变。  
- 发给 LLM 的 system 中在「长期记忆」前应包含记忆机制说明（检索、自动提取、save_memory/search_memory），且说明简短不喧宾夺主。

---

## 在 system prompt 中告知 LLM 记忆机制

**现状**：当前提示词里只有「【长期记忆】」「【本员工记忆】」的**内容**，没有说明：

- 这些内容来自**按当前问题检索**的结构化记忆库，会在多轮对话中持续保留；
- 每轮对话结束后系统会**自动从对话中提取**要点并写入记忆（人格/用户/工具/指令等类别）；
- 你有 **save_memory**、**search_memory** 工具，需要时可直接写入或检索记忆。

因此 LLM 不知道「本员工记忆」会随对话增长、也不知道可以主动调用 save_memory/search_memory，可能不会刻意用工具或表达得利于提取。

**建议**：在「长期记忆」段落**前**（或「本员工记忆」标题处）增加一段**简短说明**（1～3 句），例如：

- 说明「本员工记忆」为按当前问题从持久化记忆库中检索出的内容，会随对话自动更新；
- 说明系统会在每轮结束后自动从对话中提取要点并归类存储；
- 说明若需主动保存或查询，可使用 save_memory / search_memory 工具。

**实现位置**：在 [context.py](cli/joytrunk/agent/context.py) 的 `build_system_prompt` 中，在即将拼接 `mem_parts`（长期记忆）时，在 `parts.append("---\n【长期记忆】\n" + ...)` 之前插入一小段固定文案（可抽成常量，如 `MEMORY_SYSTEM_INSTRUCTION`）。只要会拼长期记忆就加入，文案需简短，避免占用过多 token。

**可选**：若希望由产品/运营配置这段说明，可将文案放入 config（如 `memory.prompt_instruction`）或员工 SOUL/AGENTS；首版用代码内常量即可。
