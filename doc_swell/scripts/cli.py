"""
CLI for the Ceará Swell Climatology Pipeline.

Typer is a CLI framework that builds command-line interfaces from Python
function signatures + type hints.  Think of it as Laravel's Artisan, but
auto-generated: you write a function with typed parameters, and Typer
creates the --help text, argument parsing, and validation automatically.

Alternative: argparse (stdlib).  Typer is preferred because it needs far
less boilerplate and integrates with Rich for colored output.

Usage:
    python cli.py run                  # full pipeline (steps 1–7)
    python cli.py run --from-step 4    # start at step 4
    python cli.py run --to-step 5      # stop after step 5
    python cli.py info                 # show current config
    python cli.py --help               # list all commands
"""

import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------
# App setup
#
# Typer() creates the CLI application.  Each function decorated with
# @app.command() becomes a subcommand (like `php artisan make:model`).
#
# Rich Console is Typer's companion for styled terminal output: colors,
# tables, panels.  It replaces plain print() with formatted output.
# ---------------------------------------------------------------------------
app = typer.Typer(
    name="swell",
    help="Ceará Swell Climatology Pipeline — download, validate, detect and analyze North swell events.",
    no_args_is_help=True,
)
console = Console()

# ---------------------------------------------------------------------------
# Pipeline step registry
#
# Each step maps to a script's main() function.  We import lazily (inside
# the function) to avoid loading heavy libraries like pandas/xarray when
# the user just runs `cli.py info`.
# ---------------------------------------------------------------------------
STEPS: dict[int, dict[str, str]] = {
    1: {"module": "01_validar_era5",    "label": "Validate ERA5 files"},
    2: {"module": "02_consolidar_era5", "label": "Consolidate ERA5 to CSV"},
    3: {"module": "03_baixar_ww3",      "label": "Download WW3 from ERDDAP"},
    4: {"module": "04_detectar_eventos", "label": "Detect swell events"},
    5: {"module": "05_climatologia",    "label": "Compute climatology"},
    6: {"module": "06_comparar_era5_ww3", "label": "Compare ERA5 vs WW3"},
    7: {"module": "07_relatorio",       "label": "Generate final report"},
}


def _import_step(step_num: int):
    """
    Dynamically import a pipeline step's module and return its main function.

    We use __import__ with the module name (e.g. '04_detectar_eventos').
    This works because Python allows digits in module names when imported
    programmatically, even though `import 04_detectar_eventos` would be
    a syntax error.
    """
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
    from_step: int = typer.Option(1, "--from-step", "-f", min=1, max=7, help="First step to run (1–7)"),
    to_step: int = typer.Option(7, "--to-step", "-t", min=1, max=7, help="Last step to run (1–7)"),
) -> None:
    """
    Run pipeline steps sequentially.

    By default runs all 7 steps.  Use --from-step and --to-step to run
    a subset.  Each step's output is input for the next, so skipping
    earlier steps assumes their output files already exist.

    Examples:
        python cli.py run                        # all steps
        python cli.py run --from-step 4          # steps 4–7
        python cli.py run -f 1 -t 2              # steps 1–2 only
    """
    if from_step > to_step:
        console.print(f"[red]--from-step ({from_step}) must be <= --to-step ({to_step})[/red]")
        raise typer.Exit(code=1)

    # Validate config before running anything
    _validate_config_or_exit()

    steps_to_run = {n: STEPS[n] for n in range(from_step, to_step + 1)}

    console.print()
    console.rule("[bold blue]Ceará Swell Pipeline[/bold blue]")
    console.print(f"Running steps {from_step} to {to_step} ({len(steps_to_run)} steps)\n")

    for num, step in steps_to_run.items():
        console.rule(f"[bold cyan]Step {num}/7 — {step['label']}[/bold cyan]")
        start = time.perf_counter()

        try:
            main_fn = _import_step(num)
            main_fn()
        except SystemExit as e:
            # Some scripts call sys.exit(1) on failure
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
def info() -> None:
    """
    Display the current pipeline configuration.

    Shows geographic point, year ranges, scenarios and their thresholds.
    Useful to verify settings before a full run.
    """
    cfg = _validate_config_or_exit()

    console.print()
    console.rule("[bold blue]Pipeline Configuration[/bold blue]")

    # General info
    table = Table(title="General", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("Geographic point", f"{cfg.geo_point.lat}, {cfg.geo_point.lon}")
    table.add_row("ERA5 years", f"{cfg.era5_year_start}–{cfg.era5_year_end}")
    table.add_row("WW3 years", f"{cfg.ww3_year_start}–{cfg.ww3_year_end}")
    table.add_row("Default direction", cfg.default_direction)
    table.add_row("Gap tolerance", f"{cfg.gap_tolerance_hours}h")
    table.add_row("Window durations", ", ".join(f"{d}h" for d in cfg.window_durations))
    console.print(table)
    console.print()

    # ERA5 scenarios
    era5_table = Table(title="ERA5 Scenarios")
    era5_table.add_column("Name", style="cyan")
    era5_table.add_column("Label")
    era5_table.add_column("Period min", justify="right")
    era5_table.add_column("Height min", justify="right")
    for s in cfg.scenarios_era5:
        era5_table.add_row(s.name, s.label, f"{s.period_min}s", f"{s.height_min}m")
    console.print(era5_table)
    console.print()

    # WW3 scenarios
    ww3_table = Table(title="WW3 Scenarios")
    ww3_table.add_column("Name", style="cyan")
    ww3_table.add_column("Label")
    ww3_table.add_column("Period min", justify="right")
    ww3_table.add_column("Height min", justify="right")
    for s in cfg.scenarios_ww3:
        ww3_table.add_row(s.name, s.label, f"{s.period_min}s", f"{s.height_min}m")
    console.print(ww3_table)
    console.print()

    # Pipeline steps
    steps_table = Table(title="Pipeline Steps")
    steps_table.add_column("#", justify="right", style="bold")
    steps_table.add_column("Script")
    steps_table.add_column("Description")
    for num, step in STEPS.items():
        steps_table.add_row(str(num), step["module"] + ".py", step["label"])
    console.print(steps_table)


@app.command()
def validate() -> None:
    """
    Validate ERA5 NetCDF files (step 1 only).

    Shortcut for `run --from-step 1 --to-step 1`.
    """
    _validate_config_or_exit()

    console.rule("[bold cyan]Step 1/7 — Validate ERA5 files[/bold cyan]")
    main_fn = _import_step(1)
    try:
        main_fn()
    except SystemExit as e:
        if e.code and e.code != 0:
            console.print("[red bold]Validation failed[/red bold]")
            raise typer.Exit(code=1)
    console.print("[green]Validation complete[/green]")


@app.command()
def detect(
    source: str = typer.Option("era5", "--source", "-s", help="Data source: era5 or ww3"),
) -> None:
    """
    Detect swell events (step 4).

    Currently runs the full detection for both sources; the --source
    flag is reserved for future filtering.
    """
    source_lower = source.lower()
    if source_lower not in ("era5", "ww3"):
        console.print(f"[red]Unknown source '{source}'. Use 'era5' or 'ww3'.[/red]")
        raise typer.Exit(code=1)

    _validate_config_or_exit()

    console.rule(f"[bold cyan]Step 4/7 — Detect events ({source_lower.upper()})[/bold cyan]")
    main_fn = _import_step(4)
    try:
        main_fn()
    except SystemExit as e:
        if e.code and e.code != 0:
            console.print("[red bold]Detection failed[/red bold]")
            raise typer.Exit(code=1)
    console.print("[green]Detection complete[/green]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_config_or_exit():
    """Load and validate config.  Exit with a clear error if invalid."""
    try:
        import config
        return config.get_validated_config()
    except Exception as e:
        console.print(f"[red bold]Configuration error:[/red bold]\n{e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app()
