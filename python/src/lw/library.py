"""Read and validate the stored watch library."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STORED_SCHEMA_VERSION = 0


@dataclass(frozen=True)
class Library:
    """The movie and show collections in a watch library."""

    movies: tuple[object, ...]
    shows: tuple[object, ...]


class LibraryError(ValueError):
    """A watch-library file cannot be read or does not match its schema."""


def read_library(library_path: Path) -> Library:
    """Read a version-0 empty watch library from a JSON file."""
    # A missing library is a valid empty library. `lw list` does not create it.
    if not library_path.exists():
        return Library(movies=(), shows=())

    try:
        with library_path.open(encoding="utf-8") as library_file:
            library = json.load(library_file)
    except OSError as error:
        raise LibraryError(f"Cannot read watch-library file: {library_path}") from error
    except json.JSONDecodeError as error:
        raise LibraryError(
            f"Watch-library file contains invalid JSON: {library_path}"
        ) from error

    return validate_library(library)


def validate_library(library: Any) -> Library:
    """Validate the stored version-0 empty-library schema."""
    if not isinstance(library, dict):
        raise LibraryError("Watch-library file must contain a JSON object.")
    if not all(isinstance(property_name, str) for property_name in library):
        raise LibraryError("Watch-library property names must be strings.")

    expected_properties = {"schema_version", "movies", "shows"}
    missing_properties = expected_properties - library.keys()
    unknown_properties = library.keys() - expected_properties

    if missing_properties:
        raise LibraryError("Watch-library file has missing properties.")
    if unknown_properties:
        raise LibraryError("Watch-library file has unknown properties.")
    if type(library["schema_version"]) is not int:
        raise LibraryError("Watch-library schema_version must be an integer.")
    if library["schema_version"] != STORED_SCHEMA_VERSION:
        raise LibraryError(
            "Watch-library schema version must be "
            f"{STORED_SCHEMA_VERSION}, received {library['schema_version']}."
        )
    if not isinstance(library["movies"], list) or not isinstance(
        library["shows"], list
    ):
        raise LibraryError("Watch-library movies and shows must be arrays.")
    if library["movies"] or library["shows"]:
        raise LibraryError("Version-0 watch-library collections must be empty.")

    return Library(movies=(), shows=())
