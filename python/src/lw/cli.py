"""Command-line entry point for `lw`."""

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()
ConfigPath = Annotated[
    Path | None,
    typer.Option("--config", help="Read configuration from this YAML file."),
]


@app.callback(invoke_without_command=True)
def command(context: typer.Context, config: ConfigPath = None) -> None:
    """Manage a personal watch library."""
    context.ensure_object(dict)
    context.obj["config_path"] = config

    if context.invoked_subcommand is None:
        typer.echo(context.get_help())


@app.command(name="list")
def list_items(
    context: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Write the library as JSON."),
    ] = False,
) -> None:
    """List tracked movies and shows."""
    _ = context, json_output


def main() -> None:
    """Run the `lw` command-line application."""
    app()
