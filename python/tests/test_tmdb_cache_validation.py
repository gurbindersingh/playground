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
    "data",
    [
        None,
        {"shows": {}},
        {"shows": [], "movies": {}},
        {"shows": {"Example Show": {}}, "movies": {}},
    ],
)
def test_validate_tmdb_search_cache_rejects_invalid_structure(data):
    with pytest.raises(TypeError, match=r"search\.json"):
        tmdb.validate_tmdb_search_cache(data, "search.json")


def test_validate_tmdb_selection_cache_accepts_exact_integer_ids():
    data = {"shows": {"Example Show": 1}, "movies": {"Example Movie": 2}}

    validated = tmdb.validate_tmdb_selection_cache(data, "selection.json")

    assert validated is data


@pytest.mark.parametrize("invalid_id", [True, False, "1", None])
def test_validate_tmdb_selection_cache_rejects_non_integer_ids(invalid_id):
    data = {"shows": {"Example Show": invalid_id}, "movies": {}}

    with pytest.raises(TypeError, match=r"selection\.json"):
        tmdb.validate_tmdb_selection_cache(data, "selection.json")


def test_validate_tmdb_details_cache_accepts_matching_integer_ids():
    data = {
        "shows": {"1": {"id": 1, "name": "Example Show"}},
        "movies": {"2": {"id": 2, "title": "Example Movie"}},
    }

    validated = tmdb.validate_tmdb_details_cache(data, "details.json")

    assert validated is data


@pytest.mark.parametrize(
    ("details", "expected_error"),
    [
        ({"shows": [], "movies": {}}, TypeError),
        ({"shows": {"1": []}, "movies": {}}, TypeError),
        ({"shows": {"1": {"id": True}}, "movies": {}}, TypeError),
        ({"shows": {"1": {"id": 2}}, "movies": {}}, ValueError),
        ({"shows": {"1": {}}, "movies": {}}, TypeError),
    ],
)
def test_validate_tmdb_details_cache_rejects_invalid_entries(details, expected_error):
    with pytest.raises(expected_error, match=r"details\.json"):
        tmdb.validate_tmdb_details_cache(details, "details.json")


def test_is_valid_tmdb_detail_rejects_boolean_id():
    assert not tmdb.is_valid_tmdb_detail({"id": True}, 1)
