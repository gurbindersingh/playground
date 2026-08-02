import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tv_data import main as tv_data_main


def test_main_keeps_raw_search_results_separate_from_filtered_results(monkeypatch):
    writes = {}
    downstream_search_data = []
    raw_candidates = [
        {"id": 1, "name": "Match", "original_name": "Match"},
        {"id": 2, "name": "Other", "original_name": "Other"},
    ]

    monkeypatch.setattr(tv_data_main.os.path, "exists", lambda _: False)
    monkeypatch.setattr(tv_data_main, "aggregate_show_data", lambda *_: None)
    monkeypatch.setattr(tv_data_main, "aggregate_movie_data", lambda *_: None)
    monkeypatch.setattr(tv_data_main, "sort_episodes_ascending", lambda *_: None)
    monkeypatch.setattr(tv_data_main, "deduplicate_show_episodes", lambda *_: None)

    def fake_search_for_missing(_, search_data):
        search_data["shows"]["Imported Show"] = copy.deepcopy(raw_candidates)

    def fake_filter(search_data):
        search_data["shows"]["Imported Show"] = [
            search_data["shows"]["Imported Show"][0]
        ]

    def fake_fetch_details(search_data, details):
        downstream_search_data.append(copy.deepcopy(search_data))
        return details, []

    def fake_enrich(_, search_data, __):
        downstream_search_data.append(copy.deepcopy(search_data))

    def record_write(data, path):
        writes[path] = copy.deepcopy(data)

    monkeypatch.setattr(
        tv_data_main, "search_tmdb_for_missing", fake_search_for_missing
    )
    monkeypatch.setattr(tv_data_main, "filter_tmdb_search_data", fake_filter)
    monkeypatch.setattr(tv_data_main, "fetch_details", fake_fetch_details)
    monkeypatch.setattr(tv_data_main, "enrich_watch_data", fake_enrich)
    monkeypatch.setattr(tv_data_main, "write_json", record_write)

    tv_data_main.main()

    assert writes[tv_data_main.TMDB_SEARCH_CACHE_PATH]["shows"]["Imported Show"] == (
        raw_candidates
    )
    filtered_candidates = writes[tv_data_main.TMDB_FILTERED_SEARCH_CACHE_PATH]["shows"][
        "Imported Show"
    ]
    assert filtered_candidates == [raw_candidates[0]]
    assert downstream_search_data == [
        writes[tv_data_main.TMDB_FILTERED_SEARCH_CACHE_PATH],
        writes[tv_data_main.TMDB_FILTERED_SEARCH_CACHE_PATH],
    ]
