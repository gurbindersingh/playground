import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tv_data import file_utils


def test_write_json_creates_file_with_atomic_replacement(monkeypatch, tmp_path):
    destination = tmp_path / "data.json"
    replace_calls = []
    real_replace = os.replace

    def record_replace(source, target):
        replace_calls.append((Path(source), Path(target)))
        real_replace(source, target)

    monkeypatch.setattr(file_utils, "path_from_project_root", lambda _: destination)
    monkeypatch.setattr(file_utils.os, "replace", record_replace)

    file_utils.write_json({"name": "Pokémon", "items": [1, 2]}, "ignored.json")

    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "name": "Pokémon",
        "items": [1, 2],
    }
    assert len(replace_calls) == 1
    temporary_path, replaced_destination = replace_calls[0]
    assert temporary_path.parent == destination.parent
    assert replaced_destination == destination
    assert not temporary_path.exists()


def test_write_json_replaces_existing_file(monkeypatch, tmp_path):
    destination = tmp_path / "data.json"
    destination.write_text('{"old": true}', encoding="utf-8")
    monkeypatch.setattr(file_utils, "path_from_project_root", lambda _: destination)

    file_utils.write_json({"new": True}, "ignored.json")

    assert json.loads(destination.read_text(encoding="utf-8")) == {"new": True}
    assert list(tmp_path.iterdir()) == [destination]


def test_write_json_preserves_existing_file_when_serialization_fails(
    monkeypatch, tmp_path
):
    destination = tmp_path / "data.json"
    original_contents = '{"existing": "data"}'
    destination.write_text(original_contents, encoding="utf-8")
    monkeypatch.setattr(file_utils, "path_from_project_root", lambda _: destination)

    with pytest.raises(TypeError):
        file_utils.write_json({"invalid": object()}, "ignored.json")

    assert destination.read_text(encoding="utf-8") == original_contents
    assert list(tmp_path.iterdir()) == [destination]
