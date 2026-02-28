"""记忆提取与分类 prompt（conversation + soul/user/agents/tools 类别）。"""

# 对话记忆提取：XML 输出，类别为 soul / user / agents / tools
MEMORY_EXTRACT_PROMPT = """
# 任务
从下面的对话中提取与用户或智能体相关的**可长期保留**的记忆条目。每条记忆需完整、独立、可理解。
仅提取用户明确陈述或确认的事实/偏好/习惯，不要包含助手的推测或建议。

# 记忆类别（只能使用以下名称）
{categories_str}

# 要求
- 每条记忆用一句话描述，尽量简洁（< 30 词）。
- 每条记忆必须标注一个或多个上述类别。
- 使用与对话相同的语言（中文对话则用中文）。
- 不要记录临时性、一次性信息（如“今天下雨”）；只记录有长期价值的信息。

# 输出格式（XML）
<item>
  <memory>
    <content>记忆内容 1</content>
    <categories>
      <category>user</category>
    </categories>
  </memory>
  <memory>
    <content>记忆内容 2</content>
    <categories>
      <category>soul</category>
      <category>user</category>
    </categories>
  </memory>
</item>

# 对话内容
<resource>
{resource}
</resource>
"""

# 类别摘要更新：将新记忆合并进现有摘要
CATEGORY_SUMMARY_PROMPT = """
# 任务
将「新记忆条目」合并进该主题的现有内容，生成更新后的摘要。保持 Markdown 结构，控制总长度在约 {target_length} 字以内。

# 主题
{category}

# 现有内容
<content>
{original_content}
</content>

# 新记忆条目
<item>
{new_memory_items_text}
</item>

# 输出
直接输出更新后的 Markdown 内容，不要解释或多余标记。不要包含 ```markdown 等包裹。
"""

# ---- Retrieve：LLM 排序 ----
LLM_CATEGORY_RANKER_PROMPT = """
# 任务
根据**查询**从下面列出的类别中选出最相关的至多 {top_k} 个，并按相关性从高到低排序。

# 规则
- 只包含真正与查询相关的类别。
- 最多 {top_k} 个。
- 顺序即相关性排序，第一个最相关。
- 不要编造或修改类别 ID；必须从下列列表中复制 ID。
- 若无相关类别则返回空数组。

# 输出格式（JSON）
```json
{{ "analysis": "简短分析", "categories": ["category_id_1", "category_id_2"] }}
```

# 查询
{query}

# 可选类别
{categories_data}
"""

LLM_ITEM_RANKER_PROMPT = """
# 任务
根据**查询**和已选定的相关类别，从下面的记忆条目中选出最相关的至多 {top_k} 条，并按相关性从高到低排序。

# 规则
- 只考虑属于已选类别的记忆。
- 只包含与查询真正相关的条目。
- 最多 {top_k} 条。
- 顺序即相关性排序。
- 不要编造或修改条目 ID。
- 若无相关条目则返回空数组。

# 输出格式（JSON）
```json
{{ "analysis": "简短分析", "items": ["item_id_1", "item_id_2"] }}
```

# 查询
{query}

# 已选相关类别
{relevant_categories}

# 可选记忆条目
{items_data}
"""

LLM_RESOURCE_RANKER_PROMPT = """
# 任务
根据**查询**和已有上下文，从下面的资源中选出最相关的至多 {top_k} 个，并按相关性排序。

# 规则
- 最多 {top_k} 个。
- 顺序即相关性排序。
- 不要编造或修改资源 ID。
- 若无相关资源则返回空数组。

# 输出格式（JSON）
```json
{{ "analysis": "简短分析", "resources": ["resource_id_1"] }}
```

# 查询
{query}

# 上下文
{context_info}

# 可选资源
{resources_data}
"""

__all__ = [
    "MEMORY_EXTRACT_PROMPT",
    "CATEGORY_SUMMARY_PROMPT",
    "LLM_CATEGORY_RANKER_PROMPT",
    "LLM_ITEM_RANKER_PROMPT",
    "LLM_RESOURCE_RANKER_PROMPT",
]
