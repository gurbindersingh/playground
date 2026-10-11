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


def test_list_writes_an_empty_library_as_json() -> None:
    result = CliRunner().invoke(app, ["list", "--json"])

    assert result.exit_code == 0
    assert result.stdout == '{"schema_version":0,"movies":[],"shows":[]}\n'


def test_list_writes_an_empty_library_for_the_terminal() -> None:
    result = CliRunner().invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.stdout == "No tracked items.\n"


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


def test_invalid_library_writes_only_to_stderr(tmp_path) -> None:
    library_path = tmp_path / "library.json"
    library_path.write_text("{", encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"library_path: {library_path}\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["--config", str(config_path), "list", "--json"])

    assert result.exit_code == 4
    assert result.stdout == ""
    assert "invalid JSON" in result.stderr
