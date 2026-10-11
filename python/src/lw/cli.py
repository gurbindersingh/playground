"""Command-line entry point for `lw`."""

import json
import re
from pathlib import Path
from typing import Annotated

import typer

from lw.configuration import ConfigurationError, read_configuration
from lw.library import LibraryError, read_library

# `typer.Typer()` returns an application object that stores callbacks,
# commands, options, and other CLI metadata.
#
# We can call the application object like a function because the `Typer` class
# defines Python's special `__call__` method. Calling it starts argument
# parsing and dispatches the selected callback or command.
# https://typer.tiangolo.com/tutorial/typer-app/
app = typer.Typer()

# `add_typer` registers one Typer application below another. This lets `lw add`
# group commands that create library items, while each nested command remains a
# separate Python function.
# https://typer.tiangolo.com/tutorial/subcommands/
sub_app = typer.Typer()
app.add_typer(sub_app, name="add")


def validate_title(
    _context: typer.Context, _parameter: typer.CallbackParam, values: list[str]
) -> list[str]:
    """Require exactly one non-empty title option value."""
    if len(values) != 1:
        raise typer.BadParameter("Give --title exactly once.")
    if not values[0].strip():
        raise typer.BadParameter("Give a title that is not empty.")
    return values


# A `list[str]` annotation gives this callback every title value. This command
# rejects a duplicate title instead of accepting more than one value.
# https://click.palletsprojects.com/en/stable/options/#multiple-options
ShowTitle = Annotated[
    list[str],
    typer.Option(
        "--title",
        "-t",
        help="Set the show title.",
        callback=validate_title,
    ),
]


def validate_seasons(
    _context: typer.Context, _parameter: typer.CallbackParam, values: list[str]
) -> list[str]:
    """Validate the season data supplied to the add-show stub."""
    for value in values:
        match = re.fullmatch(r"(\d+):(\d+)(?::(\d+))?", value)
        if match is None:
            raise typer.BadParameter(
                "Use SEASON:EPISODES[:AIRED_EPISODES] for each --season."
            )

        season, episodes, aired_episodes = (
            int(component) if component is not None else None
            for component in match.groups()
        )
        if season is None or season < 1:
            raise typer.BadParameter("Season numbers must be positive integers.")
        if episodes is None or episodes < 1:
            raise typer.BadParameter("Episode counts must be positive integers.")
        if aired_episodes is not None and (
            aired_episodes < 1 or aired_episodes > episodes
        ):
            raise typer.BadParameter(
                "Aired episode counts must be positive and not exceed episodes."
            )
    return values


SeasonValues = Annotated[
    list[str],
    typer.Option(
        "--season",
        "-s",
        help="Set SEASON:EPISODES[:AIRED_EPISODES]. Repeat for each season.",
        callback=validate_seasons,
    ),
]


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
    try:
        configuration = read_configuration(context.obj["config_path"])
    except ConfigurationError as error:
        # Configuration failures use the first application-specific exit code.
        # `err=True` keeps JSON stdout free of diagnostic text.
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=3) from error

    try:
        library = read_library(configuration.library_path)
    except LibraryError as error:
        # Library failures use the second application-specific exit code.
        # `err=True` keeps JSON stdout free of diagnostic text.
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=4) from error

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "schema_version": 0,
                    "movies": list(library.movies),
                    "shows": list(library.shows),
                },
                separators=(",", ":"),
            )
        )
        return

    if not library.movies and not library.shows:
        typer.echo("No tracked items.")


@sub_app.command(name="show")
def add_show(title: ShowTitle, seasons: SeasonValues) -> None:
    """Add a show to the library."""
    # This stub validates its options only. Assigning the values marks them as
    # intentionally unused until the persistence feature defines their schema.
    _ = title, seasons


# The installed `lw` command calls `main`, which then passes control to Typer
# for argument parsing and command dispatch.
# https://typer.tiangolo.com/tutorial/typer-app/#explicit-application
def main() -> None:
    """Run the `lw` command-line application."""
    app()
