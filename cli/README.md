# JoyTrunk CLI

`joytrunk` 命令行入口，提供 `joytrunk onboard`、`joytrunk gateway`、`joytrunk status`。  
安装后可与 nodejs 后端协同，作为 CLI 渠道与员工对话。

## 安装（仓库内开发）

在仓库根目录（nanobot）下，对 cli 做可编辑安装（PowerShell）：

```powershell
cd cli
pip install -e .
```

然后可直接使用：

```powershell
joytrunk --help
joytrunk onboard
```

## 路径约定

- **Windows**: `%USERPROFILE%\.joytrunk`（PowerShell: `$env:USERPROFILE\.joytrunk`）
- **Linux/macOS**: `~/.joytrunk`

配置文件：`~/.joytrunk/config.json`  
工作区：`~/.joytrunk/workspace`（含 `skills/`、`memory/`、`employees/<id>/`；模板仅存于 joytrunk 包内，不设 workspace/templates）

## 测试

```powershell
cd cli
pip install -e ".[dev]"
pytest
```

## 命令指南文档与官网部署

- 文档源位于 `joytrunk/docs/`（Markdown），随包分发；用户可通过 `joytrunk docs` 打开官网命令指南，或 `joytrunk docs --local` 本地查看。
- **构建静态站（部署为官网命令指南）**：在 `cli` 目录下安装 dev 依赖后执行：
  ```powershell
  cd cli
  pip install -e ".[dev]"
  mkdocs build
  ```
  产物在 `cli/site/`，可部署到官网 `/docs/cli` 或独立域名。构建时可从 `joytrunk/__version__` 注入版本号到 `mkdocs.yml` 的 `extra.version`，与 CLI 版本一致。
