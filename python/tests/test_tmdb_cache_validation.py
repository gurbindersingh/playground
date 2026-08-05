import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tv_data import tmdb


def test_read_tmdb_cache_reports_cache_path_for_invalid_json(monkeypatch):
    def fail_read(_):
        raise json.JSONDecodeError("expected value", "", 0)

    monkeypatch.setattr(tmdb, "read_json", fail_read)

    with pytest.raises(ValueError, match=r"data/tvtime/tmdb_search_data\.json"):
        tmdb.read_tmdb_cache("data/tvtime/tmdb_search_data.json")


def test_validate_tmdb_search_cache_accepts_candidate_lists():
    data = {
        "shows": {"Example Show": [{"id": 1}, "malformed candidate"]},
        "movies": {},
    }

    validated = tmdb.validate_tmdb_search_cache(data, "search.json")

    assert validated is data


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (None, "expected a JSON object"),
        ({"shows": {}}, "movies.*JSON object"),
        ({"shows": [], "movies": {}}, "shows.*JSON object"),
        (
            {"shows": {"Example Show": {}}, "movies": {}},
            "title to a candidate list",
        ),
    ],
)
def test_validate_tmdb_search_cache_rejects_invalid_structure(data, message):
    with pytest.raises(TypeError, match=rf"search\.json.*{message}"):
        tmdb.validate_tmdb_search_cache(data, "search.json")


def test_validate_tmdb_selection_cache_accepts_exact_integer_ids():
    data = {"shows": {"Example Show": 1}, "movies": {"Example Movie": 2}}

    validated = tmdb.validate_tmdb_selection_cache(data, "selection.json")

    assert validated is data


@pytest.mark.parametrize("invalid_id", [True, False, "1", None])
def test_validate_tmdb_selection_cache_rejects_non_integer_ids(invalid_id):
    data = {"shows": {"Example Show": invalid_id}, "movies": {}}

    with pytest.raises(TypeError, match=r"selection\.json.*integer TMDB ID"):
        tmdb.validate_tmdb_selection_cache(data, "selection.json")


def test_validate_tmdb_alternative_titles_cache_accepts_string_lists():
    data = {
        "shows": {"1": ["Localized Show"]},
        "movies": {"2": []},
    }

    validated = tmdb.validate_tmdb_alternative_titles_cache(data, "alternative.json")

    assert validated is data


@pytest.mark.parametrize(
    "invalid_entry",
    [
        {"not-an-id": ["Title"]},
        {"1": "Title"},
        {"1": ["Title", 2]},
    ],
)
def test_validate_tmdb_alternative_titles_cache_rejects_invalid_entries(
    invalid_entry,
):
    data = {"shows": invalid_entry, "movies": {}}

    with pytest.raises(TypeError, match=r"alternative\.json.*list of strings"):
        tmdb.validate_tmdb_alternative_titles_cache(data, "alternative.json")


def test_validate_tmdb_details_cache_accepts_matching_integer_ids():
    data = {
        "shows": {"1": {"id": 1, "name": "Example Show"}},
        "movies": {"2": {"id": 2, "title": "Example Movie"}},
    }

    validated = tmdb.validate_tmdb_details_cache(data, "details.json")

    assert validated is data


@pytest.mark.parametrize(
    ("details", "expected_error", "message"),
    [
        ({"shows": [], "movies": {}}, TypeError, "shows.*JSON object"),
        ({"shows": {"1": []}, "movies": {}}, TypeError, "integer detail ID"),
        (
            {"shows": {"1": {"id": True}}, "movies": {}},
            TypeError,
            "integer detail ID",
        ),
        (
            {"shows": {"1": {"id": 2}}, "movies": {}},
            ValueError,
            "does not match detail ID",
        ),
        ({"shows": {"1": {}}, "movies": {}}, TypeError, "integer detail ID"),
    ],
)
def test_validate_tmdb_details_cache_rejects_invalid_entries(
    details, expected_error, message
):
    with pytest.raises(expected_error, match=rf"details\.json.*{message}"):
        tmdb.validate_tmdb_details_cache(details, "details.json")


def test_is_valid_tmdb_detail_rejects_boolean_id():
    assert not tmdb.is_valid_tmdb_detail({"id": True}, 1)


def test_filter_tmdb_search_data_validates_existing_selection_cache(
    monkeypatch, tmp_path
):
    selection_cache_path = tmp_path / "tmdb_selection_cache.json"
    selection_cache_path.touch()
    monkeypatch.setattr(tmdb, "path_from_project_root", lambda _: selection_cache_path)
    monkeypatch.setattr(
        tmdb,
        "read_tmdb_cache",
        lambda _: {"shows": {}, "movies": []},
    )

    with pytest.raises(TypeError, match=r"tmdb_selection_cache\.json.*movies"):
        tmdb.filter_tmdb_search_data({"shows": {}, "movies": {}})
