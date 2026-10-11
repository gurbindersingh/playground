import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from lw import library


def test_missing_library_is_empty(tmp_path) -> None:
    library_path = tmp_path / "missing.json"

    result = library.read_library(library_path)

    assert result == library.Library(movies=(), shows=())
    assert not library_path.exists()


def test_version_zero_empty_library_is_loaded(tmp_path) -> None:
    library_path = tmp_path / "library.json"
    library_path.write_text(
        json.dumps({"schema_version": 0, "movies": [], "shows": []}),
        encoding="utf-8",
    )

    result = library.read_library(library_path)

    assert result == library.Library(movies=(), shows=())


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("{", "invalid JSON"),
        (json.dumps([]), "must contain a JSON object"),
        (json.dumps({"movies": [], "shows": []}), "missing properties"),
        (
            json.dumps(
                {"schema_version": 0, "movies": [], "shows": [], "extra": None}
            ),
            "unknown properties",
        ),
        (
            json.dumps({"schema_version": "0", "movies": [], "shows": []}),
            "schema_version must be an integer",
        ),
        (
            json.dumps({"schema_version": 1, "movies": [], "shows": []}),
            "schema version must be 0, received 1",
        ),
        (
            json.dumps({"schema_version": 0, "movies": {}, "shows": []}),
            "movies and shows must be arrays",
        ),
        (
            json.dumps({"schema_version": 0, "movies": [{}], "shows": []}),
            "collections must be empty",
        ),
    ],
)
def test_invalid_library_is_rejected(tmp_path, contents, message) -> None:
    library_path = tmp_path / "library.json"
    library_path.write_text(contents, encoding="utf-8")

    with pytest.raises(library.LibraryError, match=message):
        library.read_library(library_path)


def test_unreadable_library_is_rejected(monkeypatch, tmp_path) -> None:
    library_path = tmp_path / "library.json"
    library_path.write_text(
        json.dumps({"schema_version": 0, "movies": [], "shows": []}),
        encoding="utf-8",
    )

    def fail_to_open(*_args, **_kwargs):
        raise PermissionError

    monkeypatch.setattr(Path, "open", fail_to_open)

    with pytest.raises(library.LibraryError, match="Cannot read"):
        library.read_library(library_path)
