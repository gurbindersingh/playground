import json
import sys
from pathlib import Path

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
        None,
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
        None,
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
        None,
        {},
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
        None,
    )

    assert [candidate["id"] for candidate in filtered] == [1]
    assert reason == "exact title has no unique year match"


def test_filter_tmdb_candidates_uses_alternative_title():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [{"id": 1, "name": "English Title", "original_name": "Original Title"}],
        "Imported Title",
        "name",
        "original_name",
        "first_air_date",
        None,
        {1: ["Imported Title"]},
    )

    assert [candidate["id"] for candidate in filtered] == [1]
    assert reason == "alternative title"


def test_filter_tmdb_candidates_reviews_conflicting_cached_selection():
    filtered, reason = tmdb.filter_tmdb_candidates(
        [{"id": 1, "name": "Title", "first_air_date": "2000-01-01"}],
        "Imported Title",
        "name",
        "original_name",
        "first_air_date",
        1,
        {1: ["Imported Title"]},
    )

    assert [candidate["id"] for candidate in filtered] == [1]
    assert reason == "cached selection conflicts with title or year"


def test_fetch_tmdb_alternative_titles_uses_media_specific_response(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({"id": 1, "results": [{"title": "Imported Title"}]})

    monkeypatch.setenv("TMDB_TOKEN", "token")
    monkeypatch.setattr(tmdb.requests, "get", fake_get)
    monkeypatch.setattr(tmdb.time, "sleep", lambda _: None)

    titles = tmdb.fetch_tmdb_alternative_titles("shows", 1)

    assert titles == ["Imported Title"]
    assert calls == [
        (
            "https://api.themoviedb.org/3/tv/1/alternative_titles",
            {
                "headers": {"Authorization": "Bearer token"},
                "timeout": 30,
            },
        )
    ]


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
    monkeypatch.setattr(tmdb, "fetch_tmdb_alternative_titles", lambda *_: [])
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


def test_filter_tmdb_search_data_skips_and_reports_malformed_candidates(
    monkeypatch, tmp_path, capsys
):
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
    assert (
        "Skipping 2 malformed TMDB candidates for show Imported Show."
        in capsys.readouterr().out
    )


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

    tmdb.enrich_watch_data(
        aggregated_watch_data, tmdb_search_data, tmdb_details
    )

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
