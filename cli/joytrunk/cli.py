"""JoyTrunk CLI 入口：joytrunk / joytrunk onboard / joytrunk gateway / joytrunk docs / joytrunk status / joytrunk language。"""

import os
import subprocess
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

from joytrunk import __version__
from joytrunk.i18n import get_locale, has_language_config, locale_display_name, reset_locale_cache, set_locale, t

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


def _run_tui_inline(textual_app):
    """在当前终端内联运行 TUI（不占满屏，类似 OpenClaw）。Windows 或不支持时回退为全屏。"""
    try:
        return textual_app.run(inline=True)
    except (TypeError, Exception):
        return textual_app.run()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold]JoyTrunk[/bold]（喜象 Agent）[dim] v{}[/dim]\n"
            "{}\n"
            "{}".format(
                __version__,
                t("main.tagline"),
                t("main.help_hint", help_cmd="[cyan]joytrunk --help[/cyan]", onboard_cmd="[cyan]joytrunk onboard[/cyan]"),
            )
        )
        raise typer.Exit(0)


@app.command("onboard")
def onboard_cmd() -> None:
    """初始化本地配置与工作区（创建 ~/.joytrunk、config、workspace）。"""
    from joytrunk.onboard import run_onboard
    from joytrunk.tui.clack_flows import run_language_picker

    initial_locale = None
    if not has_language_config():
        result = run_language_picker()
        initial_locale = result if result in ("zh", "en") else "zh"

    root = run_onboard(initial_locale=initial_locale)
    if initial_locale is not None:
        reset_locale_cache()
    console.print("[green]✓[/green]", t("onboard.ready"))
    console.print("  ", t("onboard.root", path=f"[cyan]{root}[/cyan]"))
    console.print("  ", t("onboard.config", path=f"[cyan]{root / 'config.json'}[/cyan]"))
    console.print("  ", t("onboard.workspace", path=f"[cyan]{root / 'workspace'}[/cyan]"))
    console.print()
    console.print(Markdown(t("onboard.next", url=GATEWAY_URL)))


@app.command("gateway")
def gateway_cmd(
    port: int = typer.Option(GATEWAY_PORT, "--port", "-p", help="监听端口"),
) -> None:
    """启动本地常驻服务（cli 内本地管理后端），绑定 32890，提供网页管理界面与 API。"""
    gateway_dir = Path(__file__).resolve().parent / "gateway"
    if not (gateway_dir / "package.json").exists():
        console.print("[red]" + t("gateway.not_found", path="[cyan]joytrunk/gateway/[/cyan]") + "[/red]")
        console.print(t("gateway.upgrade"))
        raise typer.Exit(1)
    server_js = gateway_dir / "server.js"
    if not server_js.exists():
        console.print("[red]" + t("gateway.server_missing") + "[/red]")
        raise typer.Exit(1)
    node_modules = gateway_dir / "node_modules"
    if not node_modules.exists():
        console.print("[dim]" + t("gateway.installing") + "[/dim]")
        try:
            subprocess.run(
                ["npm", "install", "--omit=dev"],
                cwd=str(gateway_dir),
                env=dict(os.environ),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            console.print("[red]" + t("gateway.npm_failed") + "[/red]")
            raise typer.Exit(1)
    try:
        env = dict(os.environ)
        env["PORT"] = str(port)
        subprocess.run(["node", "server.js"], cwd=str(gateway_dir), env=env)
    except FileNotFoundError:
        console.print("[red]" + t("gateway.node_missing") + "[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print("[red]" + t("gateway.start_failed", error=e) + "[/red]")
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
            console.print("[red]" + t("docs.docs_not_found") + "[/red]")
            raise typer.Exit(1)
        console.print(str(docs_dir))
        return
    if local:
        if not docs_dir.exists():
            console.print("[red]" + t("docs.docs_not_found") + "[/red]")
            raise typer.Exit(1)
        import http.server
        import socketserver
        os.chdir(str(docs_dir))
        port = 0
        with socketserver.TCPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler) as httpd:
            port = httpd.socket.getsockname()[1]
            url = f"http://127.0.0.1:{port}/"
            console.print("[dim]" + t("docs.local_serving", url=url) + "[/dim]")
            webbrowser.open(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
        return
    webbrowser.open(DOCS_OFFICIAL_URL)
    console.print(t("docs.opened", url=f"[link={DOCS_OFFICIAL_URL}]{DOCS_OFFICIAL_URL}[/link]"))


@app.command("status")
def status_cmd() -> None:
    """查看运行状态、当前员工列表等。"""
    from joytrunk.paths import get_config_path, get_joytrunk_root
    from joytrunk.api_client import get_owner_id, get_base_url, list_employees, ensure_owner_via_gateway

    root = get_joytrunk_root()
    if not root.exists():
        console.print("[yellow]" + t("status.not_inited", cmd="[cyan]joytrunk onboard[/cyan]") + "[/yellow]")
        raise typer.Exit(1)
    config_path = get_config_path()
    if not config_path.exists():
        console.print("[yellow]" + t("status.no_config", cmd="[cyan]joytrunk onboard[/cyan]") + "[/yellow]")
        raise typer.Exit(1)
    gateway_url = get_base_url()
    console.print(t("status.root", path=f"[cyan]{root}[/cyan]"))
    console.print(t("status.gateway", url=f"[link={gateway_url}]{gateway_url}[/link]"))
    owner_id = get_owner_id() or ensure_owner_via_gateway()
    if owner_id:
        try:
            employees = list_employees(owner_id)
            if employees:
                console.print(t("status.employees"))
                for e in employees:
                    console.print(f"  - [cyan]{e['id']}[/cyan] {e.get('name', '')}")
            else:
                console.print(t("status.no_employees"))
        except Exception:
            console.print("[yellow]" + t("status.gateway_unreachable", cmd="[cyan]joytrunk gateway[/cyan]") + "[/yellow]")
    else:
        console.print("[yellow]" + t("status.no_owner", cmd="[cyan]joytrunk gateway[/cyan]") + "[/yellow]")


@app.command("chat")
def chat_cmd(
    employee_id: str = typer.Argument(None, help="员工 ID（不填则从配置或列表选择）"),
    no_tui: bool = typer.Option(False, "--no-tui", help="使用传统单行输入模式，不启动互动式 TUI"),
) -> None:
    """与指定员工对话（CLI 渠道）。不填员工 ID 时进入 TUI 显示员工列表或引导新建；--no-tui 为传统单行模式。"""
    import asyncio
    from joytrunk.api_client import ensure_owner_via_gateway, get_base_url, get_default_employee_id, get_owner_id, list_employees
    from joytrunk.agent.loop import run_employee_loop

    # 未指定员工且使用 TUI：使用 python-clack 选择/新建员工，再进入对话 TUI
    if employee_id is None and not no_tui:
        from joytrunk.tui import ChatTuiApp
        from joytrunk.tui.clack_flows import run_chat_entry

        triple = run_chat_entry()
        if triple:
            eid, oid, name = triple
            _run_tui_inline(ChatTuiApp(employee_id=eid, owner_id=oid, employee_name=name))
        return

    owner_id = get_owner_id()
    if not owner_id:
        owner_id = ensure_owner_via_gateway()
    if not owner_id:
        console.print("[yellow]" + t("chat.no_owner", cmd="[cyan]joytrunk gateway[/cyan]") + "[/yellow]")
        raise typer.Exit(1)
    try:
        employees = list_employees(owner_id)
    except Exception as e:
        console.print("[red]" + t("chat.gateway_error", error=e, cmd="[cyan]joytrunk gateway[/cyan]") + "[/red]")
        raise typer.Exit(1)
    if not employees:
        console.print("[yellow]" + t("chat.no_employees") + "[/yellow]")
        raise typer.Exit(1)
    eid = employee_id
    name = ""
    if not eid:
        default_eid = get_default_employee_id()
        if default_eid and any(e["id"] == default_eid for e in employees):
            eid = default_eid
            name = next((e.get("name") or e["id"] for e in employees if e["id"] == eid), eid)
            console.print(t("chat.with_employee_default", name=f"[cyan]{name}[/cyan]"))
        elif len(employees) == 1:
            eid = employees[0]["id"]
            name = employees[0].get("name", eid)
            console.print(t("chat.with_employee", name=f"[cyan]{name}[/cyan]"))
        else:
            console.print(t("chat.specify_employee"))
            for e in employees:
                console.print(f"  [cyan]{e['id']}[/cyan] {e.get('name', '')}")
            console.print(t("chat.example"))
            raise typer.Exit(0)
    else:
        if not any(e["id"] == eid for e in employees):
            console.print("[red]" + t("chat.employee_not_found", id=eid) + "[/red]")
            raise typer.Exit(1)
        name = next((e.get("name") or e["id"] for e in employees if e["id"] == eid), eid)

    if not no_tui:
        from joytrunk.tui import ChatTuiApp
        app = ChatTuiApp(employee_id=eid, owner_id=owner_id, employee_name=name or eid)
        _run_tui_inline(app)
        return

    console.print("[dim]" + t("chat.agent_hint") + "[/dim]")
    console.print(t("chat.prompt"))
    while True:
        try:
            text = console.input("[bold]" + t("chat.you") + "[/bold] ").strip()
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
            console.print("[bold]" + t("chat.employee") + "[/bold]", reply)
            if usage:
                console.print(
                    "[dim]" + t("chat.usage", input=usage.get("prompt_tokens", 0), output=usage.get("completion_tokens", 0)) + "[/dim]"
                )
        except Exception as ex:
            console.print("[red]" + t("chat.send_failed", error=ex) + "[/red]")


@app.command("language")
def language_cmd(
    locale_code: str = typer.Argument(None, help="zh（中文）或 en（English）；不填则进入 TUI 选择"),
) -> None:
    """配置 CLI 界面语言（中文 / 英文）。不填参数时进入 TUI：↑↓ 移动、Enter 确定。"""
    from joytrunk.i18n import SUPPORTED
    from joytrunk.tui.clack_flows import run_language_picker

    if locale_code is None or locale_code.strip() == "":
        result = run_language_picker()
        if result in ("zh", "en"):
            set_locale(result)
            reset_locale_cache()
            name = locale_display_name(result)
            console.print("[green]" + t("language.set", name=name, code=result) + "[/green]")
        else:
            code = get_locale()
            name = locale_display_name(code)
            console.print(t("language.current", name=name, code=code))
            console.print("[dim]" + t("language.usage") + "[/dim]")
        return
    code = locale_code.strip().lower()
    if code not in SUPPORTED:
        console.print("[red]" + t("language.invalid", code=code) + "[/red]")
        raise typer.Exit(1)
    set_locale(code)
    name = locale_display_name(code)
    console.print("[green]" + t("language.set", name=name, code=code) + "[/green]")


def run_app() -> None:
    app()


if __name__ == "__main__":
    run_app()
