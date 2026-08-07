import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tv_data import tmdb


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_search_tmdb_searches_all_media_and_result_pages(monkeypatch):
    calls = []
    pages = {
        ("tv", "Show", 1): {"results": [{"id": 1}], "total_pages": 2},
        ("tv", "Show", 2): {"results": [{"id": 2}], "total_pages": 2},
        ("movie", "Movie", 1): {"results": [{"id": 3}], "total_pages": 1},
    }

    def fake_get(url, **kwargs):
        media_type = url.rsplit("/", maxsplit=1)[1]
        query = kwargs["params"]["query"]
        page = kwargs["params"]["page"]
        calls.append((media_type, query, page))
        return FakeResponse(pages[(media_type, query, page)])

    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.requests, "get", fake_get)
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)

    data = tmdb.search_tmdb(
        {
            "shows": [{"name": "Show (2020)"}],
            "movies": [{"name": "Movie"}],
        }
    )

    assert calls == [
        ("tv", "Show", 1),
        ("tv", "Show", 2),
        ("movie", "Movie", 1),
    ]
    assert data == {
        "shows": {"Show (2020)": [{"id": 1}, {"id": 2}]},
        "movies": {"Movie": [{"id": 3}]},
    }


def test_search_tmdb_rejects_malformed_response_envelope(monkeypatch):
    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        tmdb.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse({"results": [], "total_pages": "one"}),
    )

    with pytest.raises(ValueError, match="positive integer total_pages"):
        tmdb.search_tmdb({"shows": [{"name": "Show"}], "movies": []})


def test_search_tmdb_skips_malformed_candidates_in_valid_response(monkeypatch):
    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        tmdb.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse(
            {
                "results": [{"id": "not an integer"}, {"id": 1, "name": "Show"}],
                "total_pages": 1,
            }
        ),
    )

    data = tmdb.search_tmdb({"shows": [{"name": "Show"}], "movies": []})

    assert data == {"shows": {"Show": [{"id": 1, "name": "Show"}]}, "movies": {}}


def test_search_tmdb_for_missing_searches_absent_and_empty_results(monkeypatch):
    aggregated = {
        "shows": [
            {"name": "Cached Show"},
            {"name": "Empty Show"},
            {"name": "New Show"},
        ],
        "movies": [{"name": "New Movie"}],
    }
    tmdb_search_data = {
        "shows": {
            "Cached Show": [{"id": 1}],
            "Empty Show": [],
        }
    }
    search_calls = []

    def fake_search(media_needing_search):
        search_calls.append(media_needing_search)
        return {
            "shows": {
                "Empty Show": [{"id": 2}],
                "New Show": [{"id": 3}],
            },
            "movies": {"New Movie": [{"id": 4}]},
        }

    monkeypatch.setattr(tmdb, "search_tmdb", fake_search)

    tmdb.search_tmdb_for_missing(aggregated, tmdb_search_data)

    assert search_calls == [
        {
            "shows": [aggregated["shows"][1], aggregated["shows"][2]],
            "movies": [aggregated["movies"][0]],
        }
    ]
    assert tmdb_search_data == {
        "shows": {
            "Cached Show": [{"id": 1}],
            "Empty Show": [{"id": 2}],
            "New Show": [{"id": 3}],
        },
        "movies": {"New Movie": [{"id": 4}]},
    }


def test_filter_tmdb_candidates_matches_original_title():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [
            {
                "id": 533514,
                "name": "Violet Evergarden: The Movie",
                "original_name": "劇場版 ヴァイオレット・エヴァーガーデン",
                "first_air_date": "2020-09-18",
            }
        ],
        "劇場版 ヴァイオレット・エヴァーガーデン",
        "name",
        "original_name",
        "first_air_date",
    )

    assert [candidate["id"] for candidate in filtered] == [533514]
    assert reason == "exact title"


def test_filter_tmdb_candidates_does_not_trust_unverified_single_result():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [{"id": 1, "name": "Unrelated Result", "original_name": "Unrelated Result"}],
        "Imported Title",
        "name",
        "original_name",
        "first_air_date",
    )

    assert filtered == [
        {"id": 1, "name": "Unrelated Result", "original_name": "Unrelated Result"}
    ]
    assert reason == "no exact title match"


def test_filter_tmdb_candidates_ignores_malformed_candidate():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [["malformed candidate"]],
        "Imported Title",
        "name",
        "original_name",
        "first_air_date",
    )

    assert filtered == []
    assert reason == "no exact title match"


def test_filter_tmdb_candidates_ignores_candidate_with_invalid_supported_field():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [{"id": 1, "name": 1}],
        "Imported Title",
        "name",
        "original_name",
        "first_air_date",
    )

    assert filtered == []
    assert reason == "no exact title match"


def test_filter_tmdb_candidates_requires_review_for_conflicting_year():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [{"id": 1, "name": "Electric Dreams", "first_air_date": "2009-09-29"}],
        "Electric Dreams (2017)",
        "name",
        "original_name",
        "first_air_date",
    )

    assert [candidate["id"] for candidate in filtered] == [1]
    assert reason == "exact title has no unique year match"


def test_choose_tmdb_match_prints_labelled_review_cards(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "skip")

    selected = tmdb.choose_tmdb_match(
        "Suits",
        "shows",
        [
            {
                "id": 37680,
                "name": "Suits",
                "original_name": "Suits",
                "first_air_date": "2011-06-23",
                "overview": "American legal drama.",
            },
            {
                "id": 83334,
                "name": "Suits",
                "original_name": "SUITS/スーツ",
                "first_air_date": "2018-10-08",
                "overview": "Japanese legal drama.",
            },
        ],
        "name",
        "original_name",
        "first_air_date",
        "exact title is ambiguous",
    )

    assert selected is None
    assert capsys.readouterr().out == (
        "Review required: exact title is ambiguous.\n"
        "Source Show: Suits\n"
        "Select the closest result, or skip.\n"
        "\n"
        "  [1] Suits\n"
        "      Released: 2011-06-23    TMDB ID: 37680\n"
        "      Overview: American legal drama.\n"
        "\n"
        "  [2] Suits\n"
        "      Original: SUITS/スーツ\n"
        "      Released: 2018-10-08    TMDB ID: 83334\n"
        "      Overview: Japanese legal drama.\n"
        "\n"
    )


def test_choose_tmdb_match_truncates_and_normalizes_overview(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "skip")
    overview = "First sentence.\n" + "x" * 120

    tmdb.choose_tmdb_match(
        "Unrelated",
        "movies",
        [{"id": 1, "title": "Candidate", "overview": overview}],
        "title",
        "original_title",
        "release_date",
        "no exact title match",
    )

    output = capsys.readouterr().out
    assert "\n" not in output.split("Overview: ", maxsplit=1)[1].split("\n", 1)[0]
    assert "Overview: First sentence. " + "x" * 101 + "...\n" in output


def test_filter_tmdb_search_data_prompts_for_unverified_single_result(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    monkeypatch.setattr(
        tmdb,
        "write_json",
        lambda data, file_path: (tmp_path / Path(file_path).name).write_text(
            json.dumps(data), encoding="utf-8"
        ),
    )
    monkeypatch.setattr("builtins.input", lambda _: "1")

    search_data = {
        "shows": {
            "Imported Title": [
                {
                    "id": 1,
                    "name": "Unrelated Result",
                    "original_name": "Unrelated Result",
                }
            ]
        },
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data["shows"]["Imported Title"] == [
        {"id": 1, "name": "Unrelated Result", "original_name": "Unrelated Result"}
    ]
    selection_cache = json.loads(
        (tmp_path / "tmdb_selection_cache.json").read_text(encoding="utf-8")
    )
    assert selection_cache["shows"]["Imported Title"] == 1
    assert not (tmp_path / "tmdb_search_data.json").exists()


def test_filter_tmdb_search_data_uses_cached_id_absent_from_search_results(
    monkeypatch, tmp_path
):
    selection_cache_path = tmp_path / "tmdb_selection_cache.json"
    selection_cache_path.write_text(
        json.dumps({"shows": {"Imported Show": 42}, "movies": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    monkeypatch.setattr(
        tmdb,
        "read_tmdb_cache",
        lambda file_path: json.loads(
            (tmp_path / Path(file_path).name).read_text(encoding="utf-8")
        ),
    )

    def fail_input(_):
        raise AssertionError("Cached IDs must not prompt")

    monkeypatch.setattr("builtins.input", fail_input)
    search_data = {
        "shows": {
            "Imported Show": [
                {"id": 7, "name": "Unrelated Show", "original_name": "Other"}
            ]
        },
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {"shows": {"Imported Show": [{"id": 42}]}, "movies": {}}


def test_filter_tmdb_search_data_uses_cached_id_despite_title_and_year_conflict(
    monkeypatch, tmp_path
):
    selection_cache_path = tmp_path / "tmdb_selection_cache.json"
    selection_cache_path.write_text(
        json.dumps({"shows": {"Imported Show (2024)": 42}, "movies": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    monkeypatch.setattr(
        tmdb,
        "read_tmdb_cache",
        lambda file_path: json.loads(
            (tmp_path / Path(file_path).name).read_text(encoding="utf-8")
        ),
    )

    def fail_input(_):
        raise AssertionError("Cached IDs must not prompt")

    monkeypatch.setattr("builtins.input", fail_input)
    search_data = {
        "shows": {
            "Imported Show (2024)": [
                {
                    "id": 42,
                    "name": "Renamed Show",
                    "original_name": "Renamed Show",
                    "first_air_date": "2000-01-01",
                }
            ]
        },
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {
        "shows": {"Imported Show (2024)": [{"id": 42}]},
        "movies": {},
    }


def test_filter_tmdb_search_data_reports_cached_null_without_prompt(
    monkeypatch, tmp_path, capsys
):
    selection_cache_path = tmp_path / "tmdb_selection_cache.json"
    selection_cache_path.write_text(
        json.dumps({"shows": {"Imported Show": None}, "movies": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    monkeypatch.setattr(
        tmdb,
        "read_tmdb_cache",
        lambda file_path: json.loads(
            (tmp_path / Path(file_path).name).read_text(encoding="utf-8")
        ),
    )

    def fail_input(_):
        raise AssertionError("Cached null values must not prompt")

    monkeypatch.setattr("builtins.input", fail_input)
    search_data = {"shows": {"Imported Show": [{"id": 7}]}, "movies": {}}

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {"shows": {"Imported Show": []}, "movies": {}}
    assert "Show Imported Show: unresolved" in capsys.readouterr().out


def test_filter_tmdb_search_data_persists_null_for_no_usable_candidates(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    cache_writes = []
    monkeypatch.setattr(
        tmdb,
        "write_json",
        lambda data, file_path: cache_writes.append((copy.deepcopy(data), file_path)),
    )
    search_data = {
        "shows": {"Unknown Show": [{"id": 0}, {"id": True}, "malformed"]},
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {"shows": {"Unknown Show": []}, "movies": {}}
    assert cache_writes == [
        ({"shows": {"Unknown Show": None}, "movies": {}}, tmdb.TMDB_SELECTION_CACHE_PATH)
    ]
    assert "Show Unknown Show: unresolved" in capsys.readouterr().out


def test_filter_tmdb_search_data_clears_skipped_review_candidates(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    cache_writes = []
    monkeypatch.setattr(
        tmdb,
        "write_json",
        lambda data, file_path: cache_writes.append((copy.deepcopy(data), file_path)),
    )
    monkeypatch.setattr("builtins.input", lambda _: "skip")
    search_data = {
        "shows": {
            "Imported Show": [
                {"id": 1, "name": "Unrelated One", "original_name": "One"},
                {"id": 2, "name": "Unrelated Two", "original_name": "Two"},
            ]
        },
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {"shows": {"Imported Show": []}, "movies": {}}
    assert cache_writes == []

    prompted_again = []
    monkeypatch.setattr("builtins.input", lambda _: prompted_again.append(True) or "skip")
    tmdb.filter_tmdb_search_data(
        {
            "shows": {
                "Imported Show": [
                    {"id": 1, "name": "Unrelated One", "original_name": "One"},
                    {"id": 2, "name": "Unrelated Two", "original_name": "Two"},
                ]
            },
            "movies": {},
        }
    )

    assert prompted_again == [True]


def test_filter_tmdb_search_data_preserves_unrelated_cache_entries_when_selected(
    monkeypatch, tmp_path
):
    selection_cache_path = tmp_path / "tmdb_selection_cache.json"
    selection_cache_path.write_text(
        json.dumps({"shows": {"Existing Show": 1}, "movies": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    monkeypatch.setattr(
        tmdb,
        "read_tmdb_cache",
        lambda file_path: json.loads(
            (tmp_path / Path(file_path).name).read_text(encoding="utf-8")
        ),
    )
    cache_writes = []
    monkeypatch.setattr(
        tmdb,
        "write_json",
        lambda data, file_path: cache_writes.append((copy.deepcopy(data), file_path)),
    )
    monkeypatch.setattr("builtins.input", lambda _: "1")
    selected_candidate = {
        "id": 2,
        "name": "Unrelated Show",
        "original_name": "Other",
    }
    search_data = {"shows": {"New Show": [selected_candidate]}, "movies": {}}

    tmdb.filter_tmdb_search_data(search_data)

    assert cache_writes == [
        (
            {"shows": {"Existing Show": 1, "New Show": 2}, "movies": {}},
            tmdb.TMDB_SELECTION_CACHE_PATH,
        )
    ]


def test_filter_tmdb_search_data_reviews_all_usable_candidates_for_year_conflict(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    review_calls = []

    def choose_second_candidate(*args):
        review_calls.append(args)
        return args[2][1]

    monkeypatch.setattr(tmdb, "choose_tmdb_match", choose_second_candidate)
    monkeypatch.setattr(tmdb, "write_json", lambda *_: None)
    exact_title_wrong_year = {
        "id": 1,
        "name": "Imported Show",
        "original_name": "Imported Show",
        "first_air_date": "2000-01-01",
    }
    unrelated_candidate = {
        "id": 2,
        "name": "Correct Year But Different Name",
        "original_name": "Different Name",
        "first_air_date": "2024-01-01",
    }
    duplicate_candidate = {
        "id": 2,
        "name": "Duplicate Candidate",
        "original_name": "Duplicate Candidate",
    }
    search_data = {
        "shows": {
            "Imported Show (2024)": [
                exact_title_wrong_year,
                unrelated_candidate,
                duplicate_candidate,
                {"id": 0},
            ]
        },
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert review_calls[0][2] == [exact_title_wrong_year, unrelated_candidate]
    assert search_data["shows"]["Imported Show (2024)"] == [unrelated_candidate]


def test_filter_tmdb_search_data_accepts_unique_original_title_and_matching_year(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )

    def fail_input(_):
        raise AssertionError("Unique direct matches must not prompt")

    monkeypatch.setattr("builtins.input", fail_input)
    candidate = {
        "id": 1,
        "name": "Localized Title",
        "original_name": "Original Title",
        "first_air_date": "2024-01-01",
    }
    search_data = {
        "shows": {"Original Title (2024)": [candidate]},
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {
        "shows": {"Original Title (2024)": [candidate]},
        "movies": {},
    }


def test_filter_tmdb_search_data_reviews_all_candidates_for_ambiguous_direct_match(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: tmp_path / Path(file_path).name,
    )
    review_calls = []

    def choose_last_candidate(*args):
        review_calls.append(args)
        return args[2][-1]

    monkeypatch.setattr(tmdb, "choose_tmdb_match", choose_last_candidate)
    monkeypatch.setattr(tmdb, "write_json", lambda *_: None)
    first_match = {"id": 1, "name": "Imported Show", "original_name": "One"}
    second_match = {"id": 2, "name": "Imported Show", "original_name": "Two"}
    unrelated_candidate = {"id": 3, "name": "Unrelated", "original_name": "Other"}
    search_data = {
        "shows": {"Imported Show": [first_match, second_match, unrelated_candidate]},
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert review_calls[0][2] == [first_match, second_match, unrelated_candidate]
    assert search_data["shows"]["Imported Show"] == [unrelated_candidate]


def test_filter_tmdb_search_data_uses_movie_fields_for_review(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    monkeypatch.setattr(tmdb, "write_json", lambda *_: None)
    review_calls = []

    def fake_choose_tmdb_match(*args):
        review_calls.append(args)
        return args[2][0]

    monkeypatch.setattr(tmdb, "choose_tmdb_match", fake_choose_tmdb_match)
    candidate = {
        "id": 2,
        "title": "Imported Movie",
        "original_title": "Imported Movie",
        "release_date": "2023-01-01",
    }
    search_data = {
        "shows": {},
        "movies": {"Imported Movie (2024)": [candidate]},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert review_calls == [
        (
            "Imported Movie (2024)",
            "movies",
            [candidate],
            "title",
            "original_title",
            "release_date",
            "exact title has no unique year match",
        )
    ]


def test_filter_tmdb_search_data_excludes_malformed_candidates(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    valid_candidate = {
        "id": 1,
        "name": "Imported Show",
        "original_name": "Imported Show",
    }
    search_data = {
        "shows": {"Imported Show": ["malformed", valid_candidate, None]},
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data["shows"]["Imported Show"] == [valid_candidate]


def test_filter_tmdb_search_data_accepts_unique_show_and_movie_matches(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    show_candidate = {
        "id": 1,
        "name": "Imported Show",
        "original_name": "Different Original Show",
    }
    movie_candidate = {
        "id": 2,
        "title": "Different Movie Title",
        "original_title": "Imported Movie",
    }
    search_data = {
        "shows": {"Imported Show": [show_candidate]},
        "movies": {"Imported Movie": [movie_candidate]},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data == {
        "shows": {"Imported Show": [show_candidate]},
        "movies": {"Imported Movie": [movie_candidate]},
    }


def test_filter_tmdb_search_data_leaves_empty_review_entries_unresolved(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    def fail_choose_tmdb_match(*_):
        raise AssertionError("Empty review entries must not prompt.")

    monkeypatch.setattr(tmdb, "choose_tmdb_match", fail_choose_tmdb_match)
    search_data = {
        "shows": {"Malformed Show": ["malformed", None]},
        "movies": {},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert search_data["shows"]["Malformed Show"] == []
    assert "Show Malformed Show: unresolved" in capsys.readouterr().out


def test_filter_tmdb_search_data_reviews_in_order_and_writes_selected_ids(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    review_calls = []
    cache_writes = []

    def fake_choose_tmdb_match(*args):
        review_calls.append((args[0], args[1]))
        return args[2][0] if args[0] == "Show Review" else None

    def fake_write_json(data, _):
        cache_writes.append(json.loads(json.dumps(data)))

    monkeypatch.setattr(tmdb, "choose_tmdb_match", fake_choose_tmdb_match)
    monkeypatch.setattr(tmdb, "write_json", fake_write_json)
    show_candidate = {
        "id": 1,
        "name": "Unrelated Show",
        "original_name": "Unrelated Show",
    }
    movie_candidate = {
        "id": 2,
        "title": "Unrelated Movie",
        "original_title": "Unrelated Movie",
    }
    search_data = {
        "shows": {"Show Review": [show_candidate]},
        "movies": {"Movie Review": [movie_candidate]},
    }

    tmdb.filter_tmdb_search_data(search_data)

    assert review_calls == [("Show Review", "shows"), ("Movie Review", "movies")]
    assert search_data == {
        "shows": {"Show Review": [show_candidate]},
        "movies": {"Movie Review": []},
    }
    assert cache_writes == [{"shows": {"Show Review": 1}, "movies": {}}]
    output = capsys.readouterr().out
    assert "\nReview [1/2]: Show Show Review\n" in output
    assert "\n\n\n" not in output


def test_filter_tmdb_search_data_preserves_prior_work_when_later_cache_write_fails(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tmdb,
        "path_from_project_root",
        lambda file_path: str(tmp_path / Path(file_path).name),
    )
    cache_writes = []

    def fake_choose_tmdb_match(*args):
        return args[2][0]

    def fake_write_json(data, file_path):
        if file_path != tmdb.TMDB_SELECTION_CACHE_PATH:
            return
        if cache_writes:
            raise OSError("disk full")
        cache_writes.append(json.loads(json.dumps(data)))

    monkeypatch.setattr(tmdb, "choose_tmdb_match", fake_choose_tmdb_match)
    monkeypatch.setattr(tmdb, "write_json", fake_write_json)
    first_candidate = {
        "id": 1,
        "name": "Unrelated First Show",
        "original_name": "Unrelated First Show",
    }
    second_candidate = {
        "id": 2,
        "name": "Unrelated Second Show",
        "original_name": "Unrelated Second Show",
    }
    search_data = {
        "shows": {
            "First Show": [first_candidate],
            "Second Show": [second_candidate],
        },
        "movies": {},
    }

    with pytest.raises(OSError, match="disk full"):
        tmdb.filter_tmdb_search_data(search_data)

    assert cache_writes == [{"shows": {"First Show": 1}, "movies": {}}]
    assert search_data == {
        "shows": {
            "First Show": [first_candidate],
            "Second Show": [second_candidate],
        },
        "movies": {},
    }


def test_fetch_details_requests_and_caches_one_detail_per_id(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({"id": 1399, "name": "Game of Thrones"})

    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.requests, "get", fake_get)
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)

    details, failures = tmdb.fetch_details(
        {
            "shows": {
                "Game of Thrones": [{"id": 1399}],
                "Game of Thrones (2011)": [{"id": 1399}],
            },
            "movies": {},
        },
        {"shows": {}, "movies": {}},
    )

    assert failures == []
    assert details["shows"]["1399"] == {"id": 1399, "name": "Game of Thrones"}
    assert calls == [
        (
            "https://api.themoviedb.org/3/tv/1399",
            {
                "headers": {"Authorization": "Bearer token"},
                "timeout": 30,
            },
        )
    ]


def test_fetch_details_reuses_valid_cache_without_token(monkeypatch):
    def fail_get(*args, **kwargs):
        raise AssertionError("Cached details must not make an API request.")

    monkeypatch.delenv("TMDB_TOKEN", raising=False)
    monkeypatch.setattr(tmdb.requests, "get", fail_get)

    cached_details = {
        "shows": {},
        "movies": {"11": {"id": 11, "title": "Star Wars"}},
    }
    details, failures = tmdb.fetch_details(
        {"shows": {}, "movies": {"Star Wars": [{"id": 11}]}},
        cached_details,
    )

    assert failures == []
    assert details is cached_details
    assert details["movies"]["11"]["title"] == "Star Wars"


def test_fetch_details_reports_invalid_detail_response(monkeypatch):
    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        tmdb.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse({"id": "not an integer"}),
    )

    details, failures = tmdb.fetch_details(
        {"shows": {"Example Show": [{"id": 1}]}, "movies": {}},
        {"shows": {}, "movies": {}},
    )

    assert details == {"shows": {}, "movies": {}}
    assert failures == [
        "Could not fetch show Example Show (1): "
        "TMDB detail response has an invalid or mismatched ID."
    ]


def test_fetch_details_writes_cache_after_every_five_requests(monkeypatch):
    cache_writes = []

    def fake_get(url, **kwargs):
        tmdb_id = int(url.rsplit("/", maxsplit=1)[1])
        return FakeResponse({"id": tmdb_id, "title": f"Movie {tmdb_id}"})

    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.requests, "get", fake_get)
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        tmdb,
        "write_json",
        lambda details, path: cache_writes.append((details.copy(), path)),
    )

    details, failures = tmdb.fetch_details(
        {
            "shows": {},
            "movies": {
                "Cached Movie": [{"id": 1}],
                **{f"Movie {tmdb_id}": [{"id": tmdb_id}] for tmdb_id in range(2, 7)},
            },
        },
        {"shows": {}, "movies": {"1": {"id": 1, "title": "Cached Movie"}}},
    )

    assert failures == []
    assert len(cache_writes) == 1
    assert cache_writes[0][1] == tmdb.TMDB_DETAILS_CACHE_PATH
    assert set(details["movies"]) == {"1", "2", "3", "4", "5", "6"}


def test_fetch_details_reports_entries_without_selected_ids(capsys, monkeypatch):
    monkeypatch.delenv("TMDB_TOKEN", raising=False)

    details, failures = tmdb.fetch_details(
        {"shows": {"Unknown Show": []}, "movies": {}},
        {"shows": {}, "movies": {}},
    )

    assert details == {"shows": {}, "movies": {}}
    assert failures == []
    output = capsys.readouterr().out
    assert "[1/1] Show: Unknown Show (no selected ID)" in output
    assert "TMDB details: 0 cached, 0 fetched, 1 unresolved, 0 failed" in output


def test_enrich_watch_data_merges_allowlisted_fields_and_episode_defaults():
    aggregated_watch_data = {
        "shows": [
            {
                "name": "Imported Show",
                "episodes_watched": [{"season": 1, "episode": 1}],
            }
        ],
        "movies": [{"name": "Imported Movie"}],
    }
    tmdb_search_data = {
        "shows": {"Imported Show": [{"id": 1}]},
        "movies": {"Imported Movie": [{"id": 2}]},
    }
    tmdb_details = {
        "shows": {
            "1": {
                "id": 1,
                "name": "Canonical Show",
                "genres": [{"name": "Drama"}],
                "status": "Ended",
                "tagline": "Excluded",
                "origin_country": ["US"],
            }
        },
        "movies": {
            "2": {
                "id": 2,
                "title": "Canonical Movie",
                "runtime": 121,
                "spoken_languages": [{"name": "English"}],
                "production_countries": [{"name": "United States"}],
            }
        },
    }

    enriched_watch_data = tmdb.enrich_watch_data(
        aggregated_watch_data, tmdb_search_data, tmdb_details
    )

    assert enriched_watch_data is aggregated_watch_data
    show_record = aggregated_watch_data["shows"][0]
    episode = show_record["episodes_watched"][0]
    movie_record = aggregated_watch_data["movies"][0]
    assert show_record["name"] == "Canonical Show"
    assert show_record["genres"] == [{"name": "Drama"}]
    assert show_record["homepage"] is None
    assert "tagline" not in show_record
    assert "origin_country" not in show_record
    assert episode == {
        "season": 1,
        "episode": 1,
        "name": None,
        "overview": None,
        "air_date": None,
        "runtime": None,
        "still_path": None,
        "vote_average": None,
        "vote_count": None,
    }
    assert movie_record["name"] == "Canonical Movie"
    assert movie_record["title"] == "Canonical Movie"
    assert movie_record["runtime"] == 121
    assert "production_countries" not in movie_record


def test_enrich_watch_data_preserves_unmatched_names_and_uses_separate_lists():
    aggregated_watch_data = {
        "shows": [
            {"name": "Unmatched One", "episodes_watched": []},
            {"name": "Unmatched Two", "episodes_watched": []},
        ],
        "movies": [],
    }

    tmdb.enrich_watch_data(
        aggregated_watch_data,
        {"shows": {"Unmatched One": [], "Unmatched Two": []}, "movies": {}},
        {"shows": {}, "movies": {}},
    )

    first_show, second_show = aggregated_watch_data["shows"]
    assert first_show["name"] == "Unmatched One"
    assert second_show["name"] == "Unmatched Two"
    assert first_show["genres"] == []
    assert first_show["genres"] is not second_show["genres"]
