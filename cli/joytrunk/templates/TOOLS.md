# Tool Usage Notes（工具使用说明）

当你需要读文件、写文件、列目录或执行命令时，请使用系统通过 function calling 提供的对应工具（如 read_file、write_file、list_dir、exec、edit_file、web_search 等）。
工具签名由系统通过 function calling 提供。
本文件记录非显而易见的约束与用法。

## 安全限制

- 命令有超时限制
- 危险命令会被拦截
- 输出可能被截断

## 工作区

- 文件访问默认限制在负责人工作区内，不得越权访问。

---

*具体工具以运行环境为准。*
