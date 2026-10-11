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


def test_config_option_precedes_the_list_subcommand(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("library_path: library.json\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["--config", str(config_path), "list"])

    assert result.exit_code == 0


def test_invalid_option_placement_is_a_usage_error() -> None:
    result = CliRunner().invoke(app, ["list", "--config", "test-config.yaml"])

    assert result.exit_code == 2
    assert "No such option" in result.output


def test_unknown_subcommand_is_a_usage_error() -> None:
    result = CliRunner().invoke(app, ["unknown"])

    assert result.exit_code == 2
    assert "No such command" in result.output


def test_invalid_configuration_writes_only_to_stderr(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("library_path: [\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["--config", str(config_path), "list", "--json"])

    assert result.exit_code == 3
    assert result.stdout == ""
    assert "invalid YAML" in result.stderr
