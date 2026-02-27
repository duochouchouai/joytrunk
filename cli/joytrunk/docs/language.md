# joytrunk language

配置 CLI 界面语言（中文或英文）。

## 用法

```bash
joytrunk language           # 显示当前语言及用法
joytrunk language zh        # 设为中文
joytrunk language en        # 设为英文
```

## 说明

- 设置会写入 `~/.joytrunk/config.json` 的 **cli.locale** 字段（值为 `zh` 或 `en`）。
- 未设置时默认为 **zh**（中文）。
- 环境变量 **JOYTRUNK_LANG** 可临时覆盖（适用于单次命令或脚本）：  
  `JOYTRUNK_LANG=en joytrunk status`

## 参见

- [index](index.md) — 命令指南首页
