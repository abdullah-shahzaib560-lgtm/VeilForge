"""
VeilForge Command Line Interface
"""

import typer
from rich.console import Console
from rich.panel import Panel

from veilforge import __version__

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


@app.command()
def scan(
    target: str = typer.Argument(..., help="Target to scan (URL or model name)"),
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy URL (e.g. socks5://127.0.0.1:9050)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """
    Run a basic security scan against a target (Coming soon).
    """
    console.print(f"[bold yellow]Scan command is under development.[/bold yellow]")
    console.print(f"Target : [cyan]{target}[/cyan]")
    if proxy:
        console.print(f"Proxy  : [cyan]{proxy}[/cyan]")
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
    console.print("\nThis feature will be available in a future release.")


if __name__ == "__main__":
    app()
