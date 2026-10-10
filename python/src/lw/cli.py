"""Command-line entry point for `lw`."""

from pathlib import Path
from typing import Annotated

import typer

# `typer.Typer()` returns an application object that stores callbacks,
# commands, options, and other CLI metadata.
#
# We can call the application object like a function because the `Typer` class
# defines Python's special `__call__` method. Calling it starts argument
# parsing and dispatches the selected callback or command.
# https://typer.tiangolo.com/tutorial/typer-app/
app = typer.Typer()


# This defines a type alias for the root `--config` option. The callback can
# use the alias instead of repeating the Python type and Typer metadata.
#
# `Path | None` accepts a path when the user gives `--config`. It uses `None`
# when the user does not give the option. `typer.Option` tells Typer that this
# parameter is a CLI option, rather than a CLI argument.
# https://typer.tiangolo.com/tutorial/options/path/
ConfigPath = Annotated[
    Path | None,
    typer.Option("--config", help="Read configuration from this YAML file."),
]


# With callbacks we can declare CLI parameters for the main CLI application
# (meaning `lw` in this instance). Typer runs a callback before every
# subcommand.
#
# The `context` object shares values between the callback and a subcommand
# without using global variables.
# https://typer.tiangolo.com/tutorial/commands/context/
#
# `invoke_without_command=True` runs this callback when `lw` has no
# subcommand. In that case, `context.invoked_subcommand` is `None`. We print
# help so that `lw` gives useful output and exits successfully.
@app.callback(invoke_without_command=True)
def command(context: typer.Context, config: ConfigPath = None) -> None:
    """Manage a personal watch library."""
    context.ensure_object(dict)
    context.obj["config_path"] = config

    if context.invoked_subcommand is None:
        typer.echo(context.get_help())


JsonOutput = Annotated[
    bool,
    typer.Option("--json", help="Write the library as JSON."),
]


# Here we create a subcommand: https://typer.tiangolo.com/tutorial/commands/#command-or-subcommand.
#
# CLI arguments are required. CLI options are optional.
# Every function argument becomes a CLI argument. Function argument with
# default values become options.
#
# However, the recommended way to declare CLI arguments and options is by using
# Annotated (Python's standard way of adding context specific metadata:
# https://docs.python.org/3/library/typing.html#typing.Annotated).
# When we do that, we can provide a default value for arguments and they become
# optional arguments, instead of options
# (https://typer.tiangolo.com/tutorial/arguments/default/#dynamic-default-value).
# We can also make CLI options required or not:
# https://typer.tiangolo.com/tutorial/options/required/.
@app.command(name="list")
def list_items(
    context: typer.Context,
    json_output: JsonOutput = False,
) -> None:
    """List tracked movies and shows."""
    _ = context, json_output


# The installed `lw` command calls `main`, which then passes control to Typer
# for argument parsing and command dispatch.
# https://typer.tiangolo.com/tutorial/typer-app/#explicit-application
def main() -> None:
    """Run the `lw` command-line application."""
    app()
