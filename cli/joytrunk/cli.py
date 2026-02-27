"""JoyTrunk CLI 入口：joytrunk / joytrunk onboard / joytrunk gateway / joytrunk docs / joytrunk status。"""

import os
import subprocess
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

from joytrunk import __version__

app = typer.Typer(
    name="joytrunk",
    help="JoyTrunk（喜象 Agent）- 本地 7×24 智能体员工，负责人通过即时通讯与员工交互",
    no_args_is_help=True,
)
console = Console()

GATEWAY_PORT = 32890
GATEWAY_URL = f"http://localhost:{GATEWAY_PORT}"

# 官方命令指南 URL（可经环境变量 JOYTRUNK_DOCS_URL 覆盖）
DOCS_OFFICIAL_URL = os.environ.get("JOYTRUNK_DOCS_URL", "https://joytrunk.com/docs/cli")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold]JoyTrunk[/bold]（喜象 Agent）[dim] v{}[/dim]\n"
            "本地智能体员工 · 负责人通过即时通讯与员工交互\n"
            "使用 [cyan]joytrunk --help[/cyan] 查看命令，[cyan]joytrunk onboard[/cyan] 初始化配置与工作区。"
            .format(__version__)
        )
        raise typer.Exit(0)


@app.command("onboard")
def onboard_cmd() -> None:
    """初始化本地配置与工作区（创建 ~/.joytrunk、config、workspace）。"""
    from joytrunk.onboard import run_onboard

    root = run_onboard()
    console.print("[green]✓[/green] JoyTrunk 工作区已就绪：")
    console.print(f"  根目录: [cyan]{root}[/cyan]")
    console.print(f"  配置文件: [cyan]{root / 'config.json'}[/cyan]")
    console.print(f"  工作区: [cyan]{root / 'workspace'}[/cyan]")
    console.print()
    console.print(
        Markdown(
            "在浏览器打开 **" + GATEWAY_URL + "** 进行员工配置与网页管理。\n"
            "若尚未启动本地服务，请先执行：`joytrunk gateway`"
        )
    )


@app.command("gateway")
def gateway_cmd(
    port: int = typer.Option(GATEWAY_PORT, "--port", "-p", help="监听端口"),
) -> None:
    """启动本地常驻服务（cli 内本地管理后端），绑定 32890，提供网页管理界面与 API。"""
    # 优先使用 cli 包内的 gateway（joytrunk/gateway/），与 nodejs 解耦
    gateway_dir = Path(__file__).resolve().parent / "gateway"
    if not (gateway_dir / "package.json").exists():
        console.print(
            "[red]未找到 cli 内 gateway。[/red] 若从源码运行，请确认 [cyan]joytrunk/gateway/[/cyan] 存在；"
        )
        console.print("若已 pip 安装，请升级：pip install -U joytrunk")
        raise typer.Exit(1)
    server_js = gateway_dir / "server.js"
    if not server_js.exists():
        console.print("[red]gateway/server.js 不存在。[/red]")
        raise typer.Exit(1)
    node_modules = gateway_dir / "node_modules"
    if not node_modules.exists():
        console.print("[dim]正在安装 gateway 依赖…[/dim]")
        try:
            subprocess.run(
                ["npm", "install", "--omit=dev"],
                cwd=str(gateway_dir),
                env=dict(os.environ),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            console.print("[red]npm install 失败。[/red] 请确保已安装 Node.js 并加入 PATH。")
            raise typer.Exit(1)
    try:
        env = dict(os.environ)
        env["PORT"] = str(port)
        subprocess.run(["node", "server.js"], cwd=str(gateway_dir), env=env)
    except FileNotFoundError:
        console.print("[red]未找到 node。[/red] 请确保已安装 Node.js 并加入 PATH。")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]启动失败:[/red] {e}")
        raise typer.Exit(1)


@app.command("docs")
def docs_cmd(
    local: bool = typer.Option(False, "--local", "-l", help="本地查看包内文档（启动临时 HTTP 服务）"),
    path_only: bool = typer.Option(False, "--path", "-p", help="仅打印文档目录路径"),
) -> None:
    """打开 JoyTrunk 命令指南（默认打开官网；--local 则本地查看包内文档）。"""
    docs_dir = Path(__file__).resolve().parent / "docs"
    if path_only:
        if not docs_dir.exists():
            console.print("[red]未找到文档目录。[/red] 请确认 joytrunk 包已正确安装。")
            raise typer.Exit(1)
        console.print(str(docs_dir))
        return
    if local:
        if not docs_dir.exists():
            console.print("[red]未找到文档目录。[/red] 请确认 joytrunk 包已正确安装。")
            raise typer.Exit(1)
        import http.server
        import socketserver
        os.chdir(str(docs_dir))
        port = 0
        with socketserver.TCPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler) as httpd:
            port = httpd.socket.getsockname()[1]
            url = f"http://127.0.0.1:{port}/"
            console.print(f"本地文档: [link={url}]{url}[/link] （Ctrl+C 停止）")
            webbrowser.open(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
        return
    webbrowser.open(DOCS_OFFICIAL_URL)
    console.print(f"已在浏览器打开命令指南: [link={DOCS_OFFICIAL_URL}]{DOCS_OFFICIAL_URL}[/link]")


@app.command("status")
def status_cmd() -> None:
    """查看运行状态、已绑定渠道、当前员工列表等。"""
    from joytrunk.paths import get_config_path, get_joytrunk_root
    from joytrunk.api_client import get_owner_id, get_base_url, list_employees

    root = get_joytrunk_root()
    if not root.exists():
        console.print("[yellow]尚未初始化。[/yellow] 请先执行： [cyan]joytrunk onboard[/cyan]")
        raise typer.Exit(1)
    config_path = get_config_path()
    if not config_path.exists():
        console.print("[yellow]配置文件不存在。[/yellow] 请执行： [cyan]joytrunk onboard[/cyan]")
        raise typer.Exit(1)
    gateway_url = get_base_url()
    console.print(f"JoyTrunk 根目录: [cyan]{root}[/cyan]")
    console.print(f"本地管理页: [link={gateway_url}]{gateway_url}[/link]")
    owner_id = get_owner_id()
    if owner_id:
        try:
            employees = list_employees(owner_id)
            if employees:
                console.print("当前员工：")
                for e in employees:
                    console.print(f"  - [cyan]{e['id']}[/cyan] {e.get('name', '')}")
            else:
                console.print("当前无员工，请在网页管理后台创建。")
        except Exception:
            console.print("无法连接 gateway，请先执行 [cyan]joytrunk gateway[/cyan] 启动服务。")
    else:
        console.print("尚未绑定负责人，请在网页管理后台注册/登录。")


@app.command("chat")
def chat_cmd(
    employee_id: str = typer.Argument(None, help="员工 ID（不填则从配置或列表选择）"),
) -> None:
    """与指定员工对话（CLI 渠道）。始终使用员工智能体：意图+提示词+历史 → 大模型（自有或 JoyTrunk Router）→ 执行返回的工具调用。需先启动 gateway。"""
    import asyncio
    from joytrunk.api_client import get_owner_id, get_default_employee_id, list_employees, get_base_url
    from joytrunk.agent.loop import run_employee_loop

    owner_id = get_owner_id()
    if not owner_id:
        console.print("[yellow]尚未绑定负责人。[/yellow] 请先打开 [link={}]{}[/link] 注册/登录。".format(get_base_url(), get_base_url()))
        raise typer.Exit(1)
    try:
        employees = list_employees(owner_id)
    except Exception as e:
        console.print(f"[red]无法连接 gateway:[/red] {e}。请先执行 [cyan]joytrunk gateway[/cyan]。")
        raise typer.Exit(1)
    if not employees:
        console.print("[yellow]当前无员工。[/yellow] 请在网页管理后台创建员工后再对话。")
        raise typer.Exit(1)
    eid = employee_id
    if not eid:
        default_eid = get_default_employee_id()
        if default_eid and any(e["id"] == default_eid for e in employees):
            eid = default_eid
            name = next((e.get("name") or e["id"] for e in employees if e["id"] == eid), eid)
            console.print("与员工 [cyan]{}[/cyan] 对话（配置默认）。输入 /exit 退出。".format(name))
        elif len(employees) == 1:
            eid = employees[0]["id"]
            console.print("与员工 [cyan]{}[/cyan] 对话。输入 /exit 退出。".format(employees[0].get("name", eid)))
        else:
            console.print("请指定员工 ID：")
            for e in employees:
                console.print("  [cyan]{}[/cyan] {}".format(e["id"], e.get("name", "")))
            console.print("示例: joytrunk chat <员工ID>")
            raise typer.Exit(0)
    else:
        if not any(e["id"] == eid for e in employees):
            console.print("[red]未找到员工 {}[/red]".format(eid))
            raise typer.Exit(1)

    console.print("[dim]员工智能体：意图+提示词+历史 → 大模型 → 执行工具。大模型为自有或 JoyTrunk Router。[/dim]")
    console.print("输入消息后回车发送，/exit 退出。")
    while True:
        try:
            text = console.input("[bold]你>[/bold] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() in ("/exit", "/quit", "exit", "quit"):
            break
        try:
            async def _progress(s: str) -> None:
                if s:
                    console.print("[dim]  [/dim]" + s[:200] + ("…" if len(s) > 200 else ""))

            reply, usage = asyncio.run(
                run_employee_loop(
                    eid,
                    owner_id,
                    text,
                    session_key="cli:direct",
                    on_progress=_progress,
                )
            )
            console.print("[bold]员工>[/bold]", reply)
            if usage:
                console.print(
                    "[dim]用量: 输入 {} / 输出 {} tokens[/dim]".format(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0),
                    )
                )
        except Exception as ex:
            console.print("[red]发送失败:[/red]", ex)


def run_app() -> None:
    app()


if __name__ == "__main__":
    run_app()
