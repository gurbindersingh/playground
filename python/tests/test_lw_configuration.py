import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from lw import configuration


def test_missing_default_configuration_uses_the_default_library_path(
    monkeypatch, tmp_path
) -> None:
    default_config_path = tmp_path / "config.yaml"
    default_library_path = tmp_path / "library.json"
    monkeypatch.setattr(configuration, "DEFAULT_CONFIG_PATH", default_config_path)
    monkeypatch.setattr(configuration, "DEFAULT_LIBRARY_PATH", default_library_path)

    result = configuration.read_configuration(None)

    assert result.library_path == default_library_path
    assert not default_config_path.exists()
    assert not default_library_path.exists()


def test_relative_library_path_is_resolved_from_configuration_directory(tmp_path) -> None:
    config_path = tmp_path / "configuration" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text("library_path: data/library.json\n", encoding="utf-8")

    result = configuration.read_configuration(config_path)

    assert result.library_path == config_path.parent / "data/library.json"


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("library_path: [\n", "invalid YAML"),
        ("- library.json\n", "must be a YAML mapping"),
        ("other_path: library.json\n", "must contain library_path"),
        ("library_path: library.json\nextra: value\n", "unknown properties"),
        ("1: library.json\n", "property names must be strings"),
        ("library_path: 1\n", "must be a path string"),
        ("library_path: ''\n", "must be a path string"),
    ],
)
def test_invalid_configuration_is_rejected(tmp_path, contents, message) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(contents, encoding="utf-8")

    with pytest.raises(configuration.ConfigurationError, match=message):
        configuration.read_configuration(config_path)


def test_missing_explicit_configuration_is_rejected(tmp_path) -> None:
    config_path = tmp_path / "missing.yaml"

    with pytest.raises(configuration.ConfigurationError, match="Cannot read"):
        configuration.read_configuration(config_path)


def test_unreadable_configuration_is_rejected(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("library_path: library.json\n", encoding="utf-8")

    def fail_to_open(*_args, **_kwargs):
        raise PermissionError

    monkeypatch.setattr(Path, "open", fail_to_open)

    with pytest.raises(configuration.ConfigurationError, match="Cannot read"):
        configuration.read_configuration(config_path)
