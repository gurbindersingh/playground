"""File helpers used by the TV Time conversion pipeline."""

import json
import os
import tempfile
from pathlib import Path

from utils.path_utils import path_from_project_root

from .models import JSONDocument


def read_json(file_path: str) -> object:
    """Decode and return a JSON file located relative to the project root.

    The returned value is not validated against an application data model.
    File access and JSON decoding errors are passed to the caller.
    """
    with open(
        path_from_project_root(file_path), mode="r", encoding="utf-8"
    ) as json_file:
        return json.load(json_file)


def write_json(data: JSONDocument, file_path: str) -> None:
    """Atomically write indented JSON to a project-relative file.

    Data is first written and flushed to a temporary file beside the
    destination. Replacing the destination only after serialization succeeds
    prevents a failed write from truncating an existing file. Serialization and
    file-system errors are passed to the caller. Temporary-file cleanup is
    attempted before the function returns or raises; a cleanup failure also
    propagates.
    """
    destination = path_from_project_root(file_path)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as json_file:
            temporary_path = Path(json_file.name)
            json.dump(data, json_file, indent=2, ensure_ascii=False)
            json_file.flush()
            os.fsync(json_file.fileno())

        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
