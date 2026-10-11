import json
from pathlib import Path
import subprocess
import sys

import pytest


# The project script points `lw` at `lw.cli:main`. A child process exercises
# argument parsing, exit codes, and the separate stdout and stderr streams.
LW_COMMAND = Path(sys.executable).with_name("lw")


def run_lw(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the installed `lw` command and capture its output."""
    return subprocess.run(
        [LW_COMMAND, *arguments],
        capture_output=True,
        check=False,
        text=True,
    )


def write_configuration(config_path: Path, library_path: str) -> None:
    """Write a configuration file that selects a watch-library path."""
    config_path.write_text(f"library_path: {library_path}\n", encoding="utf-8")


def test_installed_command_writes_help() -> None:
    result = run_lw("--help")

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert result.stderr == ""


def test_installed_command_accepts_the_add_show_stub() -> None:
    result = run_lw("add", "show", "--title", "Example", "-s", "1:8", "-s", "2:10:3")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (("add", "show"), "Missing option"),
        (("add", "show", "--title", "Example"), "Missing option"),
        (("add", "show", "--title", ""), "Give a title that is not empty."),
        (("add", "show", "--title", "Example", "--title", "Another"), "Give --title exactly once."),
        (
            ("add", "show", "--title", "Example", "--season", "first:8"),
            "Use SEASON:EPISODES",
        ),
        (
            ("add", "show", "--title", "Example", "--season", "0:8"),
            "Season numbers",
        ),
        (
            ("add", "show", "--title", "Example", "--season", "1:0"),
            "Episode counts",
        ),
        (
            ("add", "show", "--title", "Example", "--season", "1:8:0"),
            "Aired episode counts",
        ),
        (
            ("add", "show", "--title", "Example", "--season", "1:8:9"),
            "Aired episode counts",
        ),
    ],
)
def test_installed_command_rejects_invalid_add_show_options(
    arguments: tuple[str, ...], message: str
) -> None:
    result = run_lw(*arguments)

    assert result.returncode == 2
    assert result.stdout == ""
    assert message in result.stderr


@pytest.mark.parametrize(
    ("arguments", "expected_stdout"),
    [
        ((), "No tracked items.\n"),
        (("--json",), '{"schema_version":0,"movies":[],"shows":[]}\n'),
    ],
)
def test_installed_command_lists_an_empty_library(
    tmp_path: Path, arguments: tuple[str, ...], expected_stdout: str
) -> None:
    config_path = tmp_path / "config.yaml"
    library_path = tmp_path / "library.json"
    library_path.write_text(
        json.dumps({"schema_version": 0, "movies": [], "shows": []}), encoding="utf-8"
    )
    write_configuration(config_path, str(library_path))

    result = run_lw("--config", str(config_path), "list", *arguments)

    assert result.returncode == 0
    assert result.stdout == expected_stdout
    assert result.stderr == ""


def test_installed_command_resolves_a_relative_library_path(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    library_path = tmp_path / "library.json"
    library_path.write_text("{", encoding="utf-8")
    write_configuration(config_path, library_path.name)

    result = run_lw("--config", str(config_path), "list", "--json")

    assert result.returncode == 4
    assert result.stdout == ""
    assert "invalid JSON" in result.stderr


@pytest.mark.parametrize(
    "contents",
    ["library_path: [\n", "unknown: library.json\n", "library_path: []\n"],
)
def test_installed_command_reports_invalid_configuration(
    tmp_path: Path, contents: str
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(contents, encoding="utf-8")

    result = run_lw("--config", str(config_path), "list", "--json")

    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr.startswith("Error:")


@pytest.mark.parametrize(
    "library_contents",
    ["{", json.dumps([])],
)
def test_installed_command_reports_an_invalid_library(
    tmp_path: Path, library_contents: str
) -> None:
    config_path = tmp_path / "config.yaml"
    library_path = tmp_path / "library.json"
    library_path.write_text(library_contents, encoding="utf-8")
    write_configuration(config_path, str(library_path))

    result = run_lw("--config", str(config_path), "list", "--json")

    assert result.returncode == 4
    assert result.stdout == ""
    assert result.stderr.startswith("Error:")


def test_installed_command_treats_a_missing_library_as_empty(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    write_configuration(config_path, "missing-library.json")

    result = run_lw("--config", str(config_path), "list")

    assert result.returncode == 0
    assert result.stdout == "No tracked items.\n"
    assert result.stderr == ""


def test_installed_command_reports_an_unreadable_library(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    library_path = tmp_path / "library-directory"
    library_path.mkdir()
    write_configuration(config_path, str(library_path))

    result = run_lw("--config", str(config_path), "list", "--json")

    assert result.returncode == 4
    assert result.stdout == ""
    assert "Cannot read" in result.stderr
