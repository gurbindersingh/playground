"""File helpers used by the TV Time conversion pipeline."""

import json

from utils.path_utils import path_from_project_root


def read_json(file_path: str) -> object:
    """Return data read from a project-relative JSON file."""
    with open(
        path_from_project_root(file_path), mode="r", encoding="utf-8"
    ) as json_file:
        return json.load(json_file)


def write_json(data: object, file_path: str) -> None:
    """Write data as indented JSON to a project-relative file."""
    with open(
        path_from_project_root(file_path),
        mode="w",
        encoding="utf-8",
    ) as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)
