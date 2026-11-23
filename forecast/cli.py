"""
CLI for the Praia de Iracema surf forecast.

Usage:
    python cli.py check           # 7-day surf forecast
    python cli.py swell           # raw swell data table
    python cli.py tides           # tide table for the week
    python cli.py --help          # list all commands
"""

from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="iracema",
    help="Praia de Iracema surf forecast — swell + tide = should I surf?",
    no_args_is_help=True,
)
console = Console()


@app.command()
def check() -> None:
    """
    Show the 7-day surf forecast for Praia de Iracema.

    Combines swell forecast (Open-Meteo) with tide data (Mucuripe)
    and local surf rules to find surfable windows.
    """
    from surf_check import run_surf_check, direction_label

    console.print()
    console.rule("[bold blue]Praia de Iracema — Surf Forecast[/bold blue]")
    console.print("[dim]Swell: Open-Meteo Marine API | Tide: Porto de Mucuripe (Marinha)[/dim]\n")

    swell_data, tide_data, windows = run_surf_check()

    if not swell_data:
        console.print("[red]Could not fetch swell data. Check your internet connection.[/red]")
        raise typer.Exit(code=1)

    if not windows:
        console.print(Panel(
            "[yellow]No surfable windows found in the next 7 days.[/yellow]\n"
            "Conditions don't meet the minimum for Iracema:\n"
            "  - Wave energy >= 400 J/m2 from N/NE/E direction\n"
            "  - Tide below 1.5m (sandbars need to be exposed)",
            title="Flat week",
        ))
        return

    # Group windows by date for display
    table = Table(title=f"Surf windows ({len(windows)} found)")
    rating_colors = {"great": "bold green", "good": "green", "fair": "yellow"}

    table.add_column("Date", style="cyan")
    table.add_column("Time", style="bold")
    table.add_column("Rating", justify="center")
    table.add_column("Swell", justify="right")
    table.add_column("Energy", justify="right")
    table.add_column("Dir")
    table.add_column("Tide")
    table.add_column("Phase")

    for w in windows:
        rating_style = rating_colors.get(w.rating, "white")
        energy_style = "green" if w.energy_avg >= 500 else "yellow"

        date_str = w.start.strftime("%a %d %b")
        time_str = f"{w.start.strftime('%H:%M')}--{w.end.strftime('%H:%M')}"
        dir_label = direction_label(w.swell_dir_avg)

        table.add_row(
            date_str,
            time_str,
            f"[{rating_style}]{w.rating.upper()}[/{rating_style}]",
            f"{w.swell_height_avg:.1f}m",
            f"[{energy_style}]{w.energy_avg:.0f}J[/{energy_style}]",
            f"{dir_label} ({w.swell_dir_avg:.0f})",
            f"{w.tide_height_at_peak:.1f}m",
            w.tide_phase_summary,
        )

        # Show warnings below the row
        for warning in w.warnings:
            table.add_row("", "", "", "", "", "", "", f"[bold red]{warning}[/bold red]")

    console.print(table)
    console.print()

    # Summary
    best = max(windows, key=lambda w: {"great": 3, "good": 2, "fair": 1}.get(w.rating, 0))
    best_style = rating_colors.get(best.rating, "white")
    console.print(
        f"[bold]Best window:[/bold] {best.start.strftime('%a %d %b %H:%M')}--"
        f"{best.end.strftime('%H:%M')} "
        f"([{best_style}]{best.rating.upper()}[/{best_style}]) "
        f"| {best.tide_phase_summary}"
    )


@app.command()
def swell() -> None:
    """
    Show raw swell forecast data (for debugging).

    Displays the full 7-day hourly swell forecast from Open-Meteo
    without applying surf rules or tide data.
    """
    from fetch_swell import fetch_swell
    from rules import wave_energy
    from surf_check import direction_label

    console.print()
    console.rule("[bold blue]7-Day Swell Forecast[/bold blue]")
    console.print("[dim]Source: Open-Meteo Marine API (DWD global wave model)[/dim]\n")

    data = fetch_swell()

    if not data:
        console.print("[red]Could not fetch swell data.[/red]")
        raise typer.Exit(code=1)

    table = Table()
    table.add_column("Date", style="cyan")
    table.add_column("Time")
    table.add_column("Height", justify="right")
    table.add_column("Energy", justify="right")
    table.add_column("Direction")
    table.add_column("Period", justify="right")

    # Show every 3 hours to keep the table manageable
    for hour in data:
        if hour.time.hour % 3 != 0:
            continue

        energy = wave_energy(hour.height)
        # Color energy: green >= 400 (surfable threshold)
        e_style = "green" if energy >= 400 else "dim"
        dir_label = direction_label(hour.direction)

        table.add_row(
            hour.time.strftime("%a %d"),
            hour.time.strftime("%H:%M"),
            f"[{e_style}]{hour.height:.2f}m[/{e_style}]",
            f"[{e_style}]{energy:.0f}J[/{e_style}]",
            f"{dir_label} ({hour.direction:.0f}°)",
            f"{hour.period:.1f}s",
        )

    console.print(table)
    console.print(f"\n[dim]Showing every 3h. Total: {len(data)} hourly records.[/dim]")


@app.command()
def tides() -> None:
    """
    Show the tide table for the forecast period.

    Displays high and low tides from the Mucuripe port station
    for the next 7 days.
    """
    from tide_mucuripe import load_all_tides

    console.print()
    console.rule("[bold blue]Tide Table — Porto de Mucuripe[/bold blue]")
    console.print("[dim]Source: Marinha do Brasil[/dim]\n")

    all_tides = load_all_tides()
    now = datetime.now()

    # Filter to show tides from today onwards
    upcoming = [t for t in all_tides if t.time >= now.replace(hour=0, minute=0)]

    if not upcoming:
        console.print("[yellow]No tide data available for this period.[/yellow]")
        console.print("Update forecast/data/tide_mucuripe_2026.json with current dates.")
        return

    table = Table()
    table.add_column("Date", style="cyan")
    table.add_column("Time", style="bold")
    table.add_column("Height", justify="right")
    table.add_column("Type", justify="center")

    for tide in upcoming:
        type_style = "blue" if tide.type == "high" else "green"
        type_label = "HIGH" if tide.type == "high" else "LOW"

        table.add_row(
            tide.time.strftime("%a %d %b"),
            tide.time.strftime("%H:%M"),
            f"{tide.height:.2f}m",
            f"[{type_style}]{type_label}[/{type_style}]",
        )

    console.print(table)


if __name__ == "__main__":
    app()
