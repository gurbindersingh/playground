"""Read the configuration that selects the watch-library file."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# `Path` uses `/` to join a base path with a child path.
# https://docs.python.org/3/library/pathlib.html#operators
DEFAULT_CONFIG_PATH = Path.home() / ".config/playground/lw/config.yaml"
DEFAULT_LIBRARY_PATH = Path.home() / ".local/share/playground/lw/library.json"


# This creates an immutable value for the resolved watch-library path.
# `frozen=True` prevents code from changing the path after configuration loads.
# https://docs.python.org/3/library/dataclasses.html#frozen-instances
@dataclass(frozen=True)
class Configuration:
    """The resolved path of the watch-library file."""

    library_path: Path


class ConfigurationError(ValueError):
    """A configuration file cannot select a valid watch-library path."""


# `None` selects the default configuration path. `yaml.safe_load` parses YAML
# without allowing YAML tags to create Python objects.
# https://pyyaml.org/wiki/PyYAMLDocumentation
def read_configuration(config_path: Path | None) -> Configuration:
    """Read the selected YAML configuration or use the built-in default."""
    # expanduser() expands `~/` to the user's home directory. This is only
    # relevant for user supplied path.
    selected_path = (config_path or DEFAULT_CONFIG_PATH).expanduser().resolve()

    # An absent default configuration selects the default library path. This
    # read operation does not create either file. An explicitly selected path
    # does not use this fallback because it expresses user intent.
    if config_path is None and not selected_path.exists():
        return Configuration(library_path=DEFAULT_LIBRARY_PATH)

    try:
        with selected_path.open(encoding="utf-8") as configuration_file:
            configuration = yaml.safe_load(configuration_file)
    except OSError as error:
        raise ConfigurationError(
            f"Cannot read configuration file: {selected_path}"
        ) from error
    except yaml.YAMLError as error:
        raise ConfigurationError(
            f"Configuration file contains invalid YAML: {selected_path}"
        ) from error

    return Configuration(
        library_path=resolve_library_path(configuration, selected_path)
    )


# Relative `library_path` values use the configuration file directory as their
# base. Absolute paths do not use that base.
def resolve_library_path(configuration: Any, config_path: Path) -> Path:
    """Resolve the `library_path` value from a YAML configuration mapping."""
    if not isinstance(configuration, dict):
        raise ConfigurationError("Configuration must be a YAML mapping.")
    if not all(isinstance(property_name, str) for property_name in configuration):
        raise ConfigurationError("Configuration property names must be strings.")

    # Dictionary keys support set operations. Subtracting actual keys from
    # expected keys finds missing properties. Reversing the order finds unknown
    # properties. https://docs.python.org/3/library/stdtypes.html#dict-views
    expected_properties = {"library_path"}
    missing_properties = expected_properties - configuration.keys()
    unknown_properties = configuration.keys() - expected_properties

    if missing_properties:
        raise ConfigurationError("Configuration must contain library_path.")
    if unknown_properties:
        unknown_list = ", ".join(sorted(unknown_properties))
        raise ConfigurationError(
            f"Configuration contains unknown properties: {unknown_list}."
        )

    library_value = configuration["library_path"]
    if not isinstance(library_value, str) or not library_value.strip():
        raise ConfigurationError("Configuration library_path must be a path string.")

    try:
        library_path = Path(library_value).expanduser()

        if library_path.is_absolute():
            return library_path.resolve()

        return (config_path.parent / library_path).resolve()
    except (OSError, ValueError) as error:
        raise ConfigurationError("Configuration library_path is invalid.") from error
