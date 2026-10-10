import sys
from pathlib import Path

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from lw.cli import app


def test_root_command_is_available() -> None:
    result = CliRunner().invoke(app)

    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_list_help_describes_json_output() -> None:
    result = CliRunner().invoke(app, ["list", "--help"])

    assert result.exit_code == 0
    assert "--json" in result.output


def test_list_accepts_the_json_option_without_loading_files() -> None:
    result = CliRunner().invoke(app, ["list", "--json"])

    assert result.exit_code == 0


def test_config_option_precedes_the_list_subcommand() -> None:
    result = CliRunner().invoke(app, ["--config", "test-config.yaml", "list"])

    assert result.exit_code == 0


def test_invalid_option_placement_is_a_usage_error() -> None:
    result = CliRunner().invoke(app, ["list", "--config", "test-config.yaml"])

    assert result.exit_code == 2
    assert "No such option" in result.output


def test_unknown_subcommand_is_a_usage_error() -> None:
    result = CliRunner().invoke(app, ["unknown"])

    assert result.exit_code == 2
    assert "No such command" in result.output
