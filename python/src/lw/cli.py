"""Command-line entry point for `lw`."""

import typer

app = typer.Typer()


@app.callback()
def command() -> None:
    """Manage a personal watch library."""


def main() -> None:
    """Run the `lw` command-line application."""
    app()
