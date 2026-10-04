"""
VeilForge Command Line Interface
"""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from veilforge import __version__
from veilforge.connectors.dummy import DummyConnector
from veilforge.connectors.ollama import OllamaConnector
from veilforge.core.campaign import Campaign
from veilforge.probes.prompt_injection import ALL_PROBES
from veilforge.reporting.json_report import write_json_report

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


def _build_connector(provider: str, target: str, proxy: str | None = None):
    """Create the right connector for the chosen provider."""
    if provider == "ollama":
        return OllamaConnector(model=target, proxy_url=proxy)
    if provider == "dummy":
        return DummyConnector(response=target)
    raise typer.BadParameter(
        f"Unknown provider '{provider}'. Supported: ollama, dummy"
    )

async def _run_scan(provider: str, target: str, proxy: str | None, verbose: bool) -> int:
    connector = _build_connector(provider, target, proxy)

    with console.status(f"[bold yellow]Running {len(ALL_PROBES)} probes against {target}..."):
        result = await Campaign(connector, ALL_PROBES).run()

    await connector.close()

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

    path = write_json_report(result)
    console.print(f"\n[bold]Full report saved to:[/bold] [cyan]{path}[/cyan]")

    if verbose:
        for r in result.results:
            console.print(f"\n[dim]Prompt:[/dim] {r.prompt}")
            console.print(f"[dim]Response:[/dim] {r.response}")

    return 1 if result.succeeded > 0 else 0


@app.command()
def scan(
    target: str = typer.Argument(..., help="Model name (Ollama) or fixed reply text (dummy)"),
    provider: str = typer.Option("ollama", "--provider", help="Connector to use: ollama or dummy"),
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy URL (e.g. socks5://127.0.0.1:9050)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show every prompt and response"),
):
    """
    Run VeilForge's prompt injection probes against a target.
    """
    exit_code = asyncio.run(_run_scan(provider, target, proxy, verbose))
    raise typer.Exit(code=exit_code)

if __name__ == "__main__":
    app()
