from dotenv import load_dotenv
load_dotenv()

import asyncio

import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from veilforge import __version__
from veilforge.connectors.dummy import DummyConnector
from veilforge.connectors.gemini import GeminiConnector
from veilforge.connectors.ollama import OllamaConnector

# The legacy engine keeps using the original Campaign and probes.
from veilforge.core.campaign import Campaign

# The new engine is loaded separately so the legacy path keeps working even if
# the new architecture is unavailable.
try:
    from veilforge.core.orchestrator.campaign import CampaignRunner
    from veilforge.probes.categories.prompt_injection import DirectInjectionProbeNew
except Exception as _new_engine_import_error:
    CampaignRunner = None
    DirectInjectionProbeNew = None
    _NEW_ENGINE_IMPORT_ERROR: Exception | None = _new_engine_import_error
else:
    _NEW_ENGINE_IMPORT_ERROR = None

from veilforge.probes.prompt_injection import ALL_PROBES
from veilforge.reporting.json_report import write_json_report
from veilforge.reporting.html_report import write_html_report

# Probes that use the new BaseProbe/AttackSession interface.
NEW_PROBES = [DirectInjectionProbeNew] if DirectInjectionProbeNew is not None else []

app = typer.Typer(
    name="veilforge",
    help="VeilForge - Autonomous AI Red Teaming & Agentic Security Assessment Platform",
    add_completion=False,
)
console = Console()


@app.callback()
def main():
    """
    VeilForge - AI Red Teaming Platform
    """
    pass


@app.command()
def version():
    """Show the current version of VeilForge."""
    console.print(f"[bold green]VeilForge[/bold green] version [cyan]{__version__}[/cyan]")


@app.command()
def info():
    """Show basic information about VeilForge."""
    info_text = """
[bold]VeilForge[/bold] is an open-core platform for testing and securing
Large Language Models (LLMs) and autonomous AI agents.

[bold]Current Status:[/bold] Concept / Early Design
[bold]Focus:[/bold] Prompt injection, tool abuse, memory poisoning, goal hijacking

[bold]Ethical Use:[/bold] Only for authorized testing, research, and education.
"""
    console.print(Panel(info_text, title="VeilForge Info", border_style="blue"))


def _build_connector(
    provider: str,
    target: str,
    proxy: str | None = None,
    timeout: float = 120.0,
):
    """Create the right connector for the chosen provider."""
    if provider == "ollama":
        return OllamaConnector(model=target, proxy_url=proxy, timeout=timeout)
    if provider == "dummy":
        return DummyConnector(response=target)
    if provider == "gemini":
        return GeminiConnector(model=target, proxy_url=proxy, timeout=timeout)
    raise typer.BadParameter(
        f"Unknown provider '{provider}'. Supported: ollama, dummy, gemini"
    )


def _new_result_reason(result) -> str:
    """Build a readable reason for a new-style ProbeResult."""
    reasons = [
        finding.reason
        for finding in getattr(result, "findings", [])
        if getattr(finding, "attack_succeeded", False) and getattr(finding, "reason", "")
    ]
    if reasons:
        # Several turns can find the same marker.
        return "; ".join(dict.fromkeys(reasons))
    return str(getattr(result, "metadata", {}).get("reason", "") or "")


async def _run_old_engine(connector, target: str, verbose: bool) -> int:
    """Run the legacy Campaign engine."""
    with console.status(f"[bold yellow]Running {len(ALL_PROBES)} probes against {target}..."):
        result = await Campaign(connector, ALL_PROBES).run()

    table = Table(title="VeilForge Scan Results")
    table.add_column("Probe")
    table.add_column("Severity")
    table.add_column("Result")
    table.add_column("Reason")

    for r in result.results:
        if r.error:
            outcome = "[bold yellow]ERROR[/bold yellow]"
            detail = r.error
        elif r.attack_succeeded:
            outcome = "[bold red]VULNERABLE[/bold red]"
            detail = r.reason or ""
        else:
            outcome = "[green]OK[/green]"
            detail = r.reason or ""
        table.add_row(r.probe_name, r.severity, outcome, detail)

    console.print(table)

    summary = (
        f"Total: {result.total}   "
        f"[bold red]Succeeded: {result.succeeded}[/bold red]   "
        f"Errors: {result.errors}"
    )
    console.print(Panel(summary, title="Summary", border_style="red" if result.succeeded else "green"))

    if result.by_severity():
        console.print("By severity:", result.by_severity())

    json_path = write_json_report(result)
    html_path = write_html_report(result)
    console.print(f"\n[bold]JSON report:[/bold] [cyan]{json_path}[/cyan]")
    console.print(f"[bold]HTML report:[/bold] [cyan]{html_path}[/cyan]")

    if verbose:
        for r in result.results:
            console.print(f"\n[dim]Prompt:[/dim] {r.prompt}")
            console.print(f"[dim]Response:[/dim] {r.response}")

    return 1 if result.succeeded > 0 else 0


async def _run_new_engine(connector, target: str, verbose: bool) -> int:
    """Run the CampaignRunner/AttackSession engine with new-style probes."""
    if CampaignRunner is None or not NEW_PROBES:
        console.print("[bold red]The new engine is not available.[/bold red]")
        if _NEW_ENGINE_IMPORT_ERROR is not None:
            console.print(f"[dim]{_NEW_ENGINE_IMPORT_ERROR}[/dim]")
        return 1

    try:
        with console.status(f"[bold yellow]Running {len(NEW_PROBES)} probes against {target} (new engine)..."):
            # CampaignRunner creates and manages the AttackSession internally.
            runner = CampaignRunner(connector, NEW_PROBES)
            result = await runner.run()
    except Exception as e:
        console.print(f"[bold red]New engine failed:[/bold red] {e}")
        return 1

    table = Table(title="VeilForge Scan Results (New Engine)")
    table.add_column("Probe")
    table.add_column("Severity")
    table.add_column("Result")
    table.add_column("Reason")

    for r in result.results:
        if getattr(r, "error", None):
            outcome = "[bold yellow]ERROR[/bold yellow]"
            detail = r.error
        elif getattr(r, "attack_succeeded", False):
            outcome = "[bold red]VULNERABLE[/bold red]"
            detail = _new_result_reason(r)
        else:
            outcome = "[green]OK[/green]"
            detail = _new_result_reason(r)
        table.add_row(
            getattr(r, "probe_name", ""),
            getattr(r, "severity", ""),
            outcome,
            detail[:80],
        )

    console.print(table)

    summary = (
        f"Total: {result.total}   "
        f"[bold red]Succeeded: {result.succeeded}[/bold red]   "
        f"Errors: {result.errors}"
    )
    console.print(Panel(summary, title="Summary", border_style="red" if result.succeeded else "green"))

    if hasattr(result, "by_severity"):
        severity_counts = result.by_severity()
        if severity_counts:
            console.print("By severity:", severity_counts)

    json_path = write_json_report(result)
    html_path = write_html_report(result)
    console.print(f"\n[bold]JSON report:[/bold] [cyan]{json_path}[/cyan]")
    console.print(f"[bold]HTML report:[/bold] [cyan]{html_path}[/cyan]")

    if verbose:
        for r in result.results:
            for t in getattr(r, "turns", []):
                user_message = getattr(t, "user_message", None)
                console.print(f"\n[dim]Prompt:[/dim] {getattr(user_message, 'content', '')}")
                console.print(f"[dim]Response:[/dim] {getattr(t, 'response_text', '')}")

    return 1 if result.succeeded > 0 else 0


async def _run_scan(
    provider: str,
    target: str,
    proxy: str | None,
    verbose: bool,
    timeout: float = 120.0,
    engine: str = "old",
) -> int:
    engine = engine.lower()
    if engine not in ("old", "new"):
        raise typer.BadParameter(
            f"Unknown engine '{engine}'. Supported: old, new", param_hint="--engine"
        )

    connector = _build_connector(provider, target, proxy, timeout)
    try:
        if engine == "new":
            return await _run_new_engine(connector, target, verbose)
        return await _run_old_engine(connector, target, verbose)
    finally:
        await connector.close()


@app.command()
def scan(
    target: str = typer.Argument(..., help="Model name (Ollama) or fixed reply text (dummy)"),
    provider: str = typer.Option("ollama", "--provider", help="Connector to use: ollama, dummy, gemini"),
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy URL (e.g. socks5://127.0.0.1:9050)"),
    timeout: float = typer.Option(120.0, "--timeout", "-t", help="Request timeout in seconds"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show every prompt and response"),
    engine: str = typer.Option(
        "old",
        "--engine",
        help="Scan engine: old (legacy) or new (CampaignRunner/AttackSession with new probes)",
    ),
):
    """
    Run VeilForge's prompt injection probes against a target.
    """
    exit_code = asyncio.run(_run_scan(provider, target, proxy, verbose, timeout, engine=engine))
    raise typer.Exit(code=exit_code)

if __name__ == "__main__":
    app()
