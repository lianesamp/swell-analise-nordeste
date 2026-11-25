"""
CLI for the Season Analysis Pipeline (Front 3).

Same pattern as the March pipeline's cli.py: Typer CLI with Rich output.
Each step maps to a script's main() function, imported lazily.

Usage:
    python cli.py run                  # full pipeline (steps 1-3)
    python cli.py run --from-step 2    # start at step 2
    python cli.py consolidate          # step 1 only
    python cli.py detect               # step 2 only
    python cli.py climatology          # step 3 only
    python cli.py info                 # show config
    python cli.py --help               # list commands
"""

import time

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="season",
    help="Season Swell Analysis Pipeline (Front 3) — consolidate, detect events and compute monthly climatology.",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Pipeline step registry
# ---------------------------------------------------------------------------
STEPS: dict[int, dict[str, str]] = {
    1: {"module": "01_consolidar_season",         "label": "Consolidate NetCDF to CSV"},
    2: {"module": "02_detectar_eventos_season",   "label": "Detect swell events"},
    3: {"module": "03_climatologia_mensal",       "label": "Compute monthly climatology"},
}


def _import_step(step_num: int):
    """Dynamically import a pipeline step's module and return its main function."""
    module_name = STEPS[step_num]["module"]
    try:
        mod = __import__(module_name)
    except ImportError as e:
        console.print(f"[red]Error importing step {step_num} ({module_name}): {e}[/red]")
        raise typer.Exit(code=1)

    if not hasattr(mod, "main"):
        console.print(f"[red]Step {step_num} ({module_name}) has no main() function[/red]")
        raise typer.Exit(code=1)

    return mod.main


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def run(
    from_step: int = typer.Option(1, "--from-step", "-f", min=1, max=3, help="First step to run (1-3)"),
    to_step: int = typer.Option(3, "--to-step", "-t", min=1, max=3, help="Last step to run (1-3)"),
) -> None:
    """
    Run pipeline steps sequentially.

    By default runs all 3 steps.  Use --from-step and --to-step to run
    a subset.

    Examples:
        python cli.py run                  # all steps
        python cli.py run --from-step 2    # steps 2-3
        python cli.py run -f 1 -t 1        # step 1 only
    """
    if from_step > to_step:
        console.print(f"[red]--from-step ({from_step}) must be <= --to-step ({to_step})[/red]")
        raise typer.Exit(code=1)

    steps_to_run = {n: STEPS[n] for n in range(from_step, to_step + 1)}

    console.print()
    console.rule("[bold blue]Season Swell Pipeline (Front 3)[/bold blue]")
    console.print(f"Running steps {from_step} to {to_step} ({len(steps_to_run)} steps)\n")

    for num, step in steps_to_run.items():
        console.rule(f"[bold cyan]Step {num}/3 — {step['label']}[/bold cyan]")
        start = time.perf_counter()

        try:
            main_fn = _import_step(num)
            main_fn()
        except SystemExit as e:
            if e.code and e.code != 0:
                console.print(f"\n[red bold]Step {num} failed (exit code {e.code})[/red bold]")
                raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"\n[red bold]Step {num} failed: {e}[/red bold]")
            raise typer.Exit(code=1)

        elapsed = time.perf_counter() - start
        console.print(f"\n[green]Step {num} completed[/green] ({elapsed:.1f}s)\n")

    console.rule("[bold green]Pipeline complete[/bold green]")


@app.command()
def consolidate() -> None:
    """Consolidate season NetCDF files into CSV (step 1)."""
    console.rule("[bold cyan]Step 1/3 — Consolidate NetCDF to CSV[/bold cyan]")
    main_fn = _import_step(1)
    try:
        main_fn()
    except SystemExit as e:
        if e.code and e.code != 0:
            raise typer.Exit(code=1)
    console.print("[green]Consolidation complete[/green]")


@app.command()
def detect() -> None:
    """Detect swell events from season data (step 2)."""
    console.rule("[bold cyan]Step 2/3 — Detect swell events[/bold cyan]")
    main_fn = _import_step(2)
    try:
        main_fn()
    except SystemExit as e:
        if e.code and e.code != 0:
            raise typer.Exit(code=1)
    console.print("[green]Event detection complete[/green]")


@app.command()
def climatology() -> None:
    """Compute monthly climatology from detected events (step 3)."""
    console.rule("[bold cyan]Step 3/3 — Monthly climatology[/bold cyan]")
    main_fn = _import_step(3)
    try:
        main_fn()
    except SystemExit as e:
        if e.code and e.code != 0:
            raise typer.Exit(code=1)
    console.print("[green]Climatology complete[/green]")


@app.command()
def info() -> None:
    """Display season pipeline configuration."""
    import config as cfg

    console.print()
    console.rule("[bold blue]Season Pipeline Configuration (Front 3)[/bold blue]")

    # General
    table = Table(title="General", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("Geographic point", f"{cfg.LAT}, {cfg.LON}")
    table.add_row("Season months", ", ".join(str(m) for m in cfg.SEASON_MONTHS))
    table.add_row("Year range", f"{cfg.SEASON_YEAR_START}-{cfg.SEASON_YEAR_END}")
    table.add_row("Direction filter", cfg.DEFAULT_DIRECTION)
    table.add_row("Gap tolerance", f"{cfg.GAP_TOLERANCE_HOURS}h")
    table.add_row("Raw data dir", cfg.RAW_DIR)
    table.add_row("Output CSV", cfg.SEASON_CSV)
    console.print(table)
    console.print()

    # Scenarios
    sc_table = Table(title="ERA5 Scenarios")
    sc_table.add_column("Name", style="cyan")
    sc_table.add_column("Label")
    sc_table.add_column("Period min", justify="right")
    sc_table.add_column("Height min", justify="right")
    for s in cfg.SCENARIOS_ERA5:
        sc_table.add_row(s["name"], s["label"], f"{s['period_min']}s", f"{s['height_min']}m")
    console.print(sc_table)
    console.print()

    # Steps
    steps_table = Table(title="Pipeline Steps")
    steps_table.add_column("#", justify="right", style="bold")
    steps_table.add_column("Script")
    steps_table.add_column("Description")
    for num, step in STEPS.items():
        steps_table.add_row(str(num), step["module"] + ".py", step["label"])
    console.print(steps_table)


if __name__ == "__main__":
    app()
