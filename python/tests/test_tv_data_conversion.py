import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tv_data import tv_data


@pytest.mark.parametrize(
    ("alternate_episode", "expected_episode_numbers"),
    [("1", [1]), ("2", [1, 2])],
)
def test_aggregate_show_data_reads_both_episode_column_formats(
    monkeypatch, alternate_episode, expected_episode_numbers
):
    rows = [
        {
            "series_name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": "",
            "ep_watch_count": "",
            "s_no": "1",
            "ep_no": "1",
            "season_number": "1",
            "episode_number": alternate_episode,
        }
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_show_data({}, "ignored.csv")

    assert [
        episode["episode"]
        for episode in aggregated["Example Show"]["episodes_watched"]
    ] == expected_episode_numbers


def test_aggregate_show_data_merges_timestamps_archive_and_episode_columns(monkeypatch):
    rows = [
        {
            "series_name": " Example Show ",
            "created_at": "2024-02-01 10:00:00",
            "updated_at": "2024-02-02 10:00:00",
            "is_archived": "false",
            "ep_watch_count": "2",
            "s_no": "1",
            "ep_no": "1",
            "season_number": "",
            "episode_number": "",
        },
        {
            "series_name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-03-02 10:00:00",
            "is_archived": "true",
            "ep_watch_count": "3",
            "s_no": "",
            "ep_no": "",
            "season_number": "1",
            "episode_number": "2",
        },
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_show_data({}, "ignored.csv")

    assert aggregated == {
        "Example Show": {
            "name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-03-02 10:00:00",
            "is_archived": True,
            "episodes_watched": [
                {"season": 1, "episode": 1, "updated_at": "2024-02-02 10:00:00"},
                {"season": 1, "episode": 2, "updated_at": "2024-03-02 10:00:00"},
            ],
        }
    }


def test_aggregate_show_data_ignores_reported_episode_count(monkeypatch):
    rows = [
        {
            "series_name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": "false",
            "ep_watch_count": "1",
        },
        {
            "series_name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-02-01 10:00:00",
            "is_archived": "",
            "ep_watch_count": "99",
        },
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_show_data({}, "ignored.csv")

    assert aggregated["Example Show"]["updated_at"] == "2024-01-02 10:00:00"
    assert "total_episodes_watched" not in aggregated["Example Show"]


def test_aggregate_show_data_does_not_replace_newer_archive_status(monkeypatch):
    rows = [
        {
            "series_name": "Example Show",
            "updated_at": "2024-03-01 10:00:00",
            "is_archived": "true",
        },
        {
            "series_name": "Example Show",
            "updated_at": "2024-02-01 10:00:00",
            "is_archived": "false",
        },
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_show_data({}, "ignored.csv")

    assert aggregated["Example Show"]["updated_at"] == "2024-03-01 10:00:00"
    assert aggregated["Example Show"]["is_archived"] is True


def test_aggregate_show_data_reports_blank_name_with_csv_row(monkeypatch, capsys):
    rows = [
        {"series_name": "   "},
        {
            "series_name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": "false",
        },
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_show_data({}, "shows.csv")

    assert list(aggregated) == ["Example Show"]
    assert (
        "Skipping blank show name in shows.csv at CSV row 2." in capsys.readouterr().out
    )


def test_aggregate_movie_data_keeps_earliest_creation_and_latest_update(monkeypatch):
    rows = [
        {
            "movie_name": "Example Movie",
            "created_at": "2024-02-01 10:00:00",
            "updated_at": "2024-02-02 10:00:00",
        },
        {
            "movie_name": "Example Movie",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-03-02 10:00:00",
        },
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_movie_data({}, "ignored.csv")

    assert aggregated["Example Movie"] == {
        "name": "Example Movie",
        "created_at": "2024-01-01 10:00:00",
        "updated_at": "2024-03-02 10:00:00",
        "watched": True,
    }


def test_aggregate_movie_data_reports_blank_name_with_csv_row(monkeypatch, capsys):
    rows = [
        {"movie_name": "\t"},
        {
            "movie_name": "Example Movie",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
        },
    ]
    monkeypatch.setattr(tv_data, "read_csv_rows", lambda _: rows)

    aggregated = tv_data.aggregate_movie_data({}, "movies.csv")

    assert list(aggregated) == ["Example Movie"]
    assert (
        "Skipping blank movie name in movies.csv at CSV row 2."
        in capsys.readouterr().out
    )


def test_sort_episodes_ascending_orders_by_season_and_episode():
    shows = {
        "Example Show": {
            "name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": False,
            "episodes_watched": [
                {"season": 2, "episode": 1, "updated_at": "2024-01-02 10:00:00"},
                {"season": 1, "episode": 2, "updated_at": "2024-01-02 10:00:00"},
                {"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"},
            ],
        },
        "Empty Show": {
            "name": "Empty Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": False,
            "episodes_watched": [],
        },
    }

    tv_data.sort_episodes_ascending(shows)

    assert [
        (episode["season"], episode["episode"])
        for episode in shows["Example Show"]["episodes_watched"]
    ] == [(1, 1), (1, 2), (2, 1)]
    assert shows["Empty Show"]["episodes_watched"] == []


def test_deduplicate_show_episodes_removes_duplicate_and_zero_episode_entries():
    shows = [
        {
            "name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": False,
            "episodes_watched": [
                {"season": 1, "episode": 1, "updated_at": "2024-01-01 10:00:00"},
                {"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"},
                {"season": 0, "episode": 0, "updated_at": "2024-01-02 10:00:00"},
            ],
        }
    ]

    tv_data.deduplicate_show_episodes(shows)

    assert shows[0]["episodes_watched"] == [
        {"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"}
    ]


@pytest.mark.parametrize(
    ("episodes", "expected_episodes"),
    [
        (
            [
                {"season": 1, "episode": 1, "updated_at": "2024-01-01 10:00:00"},
                {"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"},
            ],
            [{"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"}],
        ),
        (
            [
                {"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"},
                {"season": 1, "episode": 1, "updated_at": "2024-01-01 10:00:00"},
            ],
            [{"season": 1, "episode": 1, "updated_at": "2024-01-02 10:00:00"}],
        ),
        (
            [{"season": 0, "episode": 0, "updated_at": "2024-01-01 10:00:00"}],
            [],
        ),
    ],
)
def test_deduplicate_show_episodes_always_cleans_episode_list(
    episodes, expected_episodes
):
    shows = [
        {
            "name": "Example Show",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 10:00:00",
            "is_archived": False,
            "episodes_watched": episodes,
        }
    ]

    tv_data.deduplicate_show_episodes(shows)

    assert shows[0]["episodes_watched"] == expected_episodes


def test_deduplicate_episodes_returns_ascending_season_and_episode_order():
    episodes = [
        {"season": 2, "episode": 1, "updated_at": "2024-01-03 10:00:00"},
        {"season": 1, "episode": 2, "updated_at": "2024-01-02 10:00:00"},
        {"season": 1, "episode": 1, "updated_at": "2024-01-01 10:00:00"},
    ]

    deduplicated = tv_data.deduplicate_episodes(episodes)

    assert [(episode["season"], episode["episode"]) for episode in deduplicated] == [
        (1, 1),
        (1, 2),
        (2, 1),
    ]


def test_deduplicate_episodes_keeps_first_entry_when_timestamps_are_equal():
    first_episode = {
        "season": 1,
        "episode": 1,
        "updated_at": "2024-01-01 10:00:00",
        "name": "First",
    }
    second_episode = {
        "season": 1,
        "episode": 1,
        "updated_at": "2024-01-01 10:00:00",
        "name": "Second",
    }

    deduplicated = tv_data.deduplicate_episodes([first_episode, second_episode])

    assert deduplicated == [first_episode]
