"""CLI entry point for DeFi Risk Scanner."""
from __future__ import annotations
from pathlib import Path

import click

from .protocols import lookup_protocol, list_protocols, PROTOCOLS
from .analyzer import analyze_protocol
from .reporter import format_markdown, print_terminal
from .ai_analyzer import ai_analyze_risk, get_api_key


@click.group()
@click.version_option(version="0.1.0", prog_name="defi-risk")
def main():
    """DeFi Risk Scanner — AI-powered protocol risk analysis.

    Scans DeFi protocols for risk factors and generates a risk score (A-F).
    """
    pass


@main.command()
@click.argument("protocol")
@click.option("--chain", "-c", default="ethereum", help="Blockchain (ethereum, bsc, arbitrum)")
@click.option("--format", "-f", "fmt", type=click.Choice(["terminal", "markdown"]), default="terminal")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path")
@click.option("--ai", is_flag=True, help="Enable AI-powered deep analysis (requires MIMO_API_KEY)")
def scan(protocol, chain, fmt, output, ai):
    """Scan a DeFi protocol for risk factors.

    PROTOCOL can be a name (uniswap, aave) or contract address.
    """
    # Lookup protocol
    proto = lookup_protocol(protocol)
    if not proto:
        click.echo(f"Protocol '{protocol}' not found in database.")
        click.echo("Use 'defi-risk list' to see supported protocols.")
        click.echo("Or scan by contract address: defi-risk scan 0x... --chain ethereum")
        return

    click.echo(f"Scanning {proto.name} ({proto.chain})...")
    click.echo(f"Contract: {proto.main_contract}")
    click.echo()

    # Run analysis
    report = analyze_protocol(proto)

    # Output
    if fmt == "markdown":
        md = format_markdown(report)
        if output:
            Path(output).write_text(md, encoding="utf-8")
            click.echo(f"Report written to {output}")
        else:
            click.echo(md)
    else:
        print_terminal(report)

    # AI analysis
    if ai:
        api_key = get_api_key()
        if not api_key:
            click.echo("\nWarning: MIMO_API_KEY not set. Skipping AI analysis.", err=True)
        else:
            click.echo("\nRunning AI analysis...")
            ai_report = ai_analyze_risk(report)
            if ai_report:
                click.echo()
                click.echo("--- AI Deep Analysis ---")
                click.echo(ai_report)


@main.command("list")
def list_cmd():
    """List all supported protocols."""
    protocols = list_protocols()
    click.echo(f"Supported protocols ({len(protocols)}):\n")
    for p in protocols:
        exploits = " [HAS EXPLOITS]" if p.exploits else ""
        click.echo(f"  {p.name:20s} {p.chain:12s} {p.category:12s} {p.slug}{exploits}")
    click.echo(f"\nUse: defi-risk scan <name>")


if __name__ == "__main__":
    main()
