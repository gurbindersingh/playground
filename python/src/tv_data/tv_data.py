"""Convert TV Time CSV exports into JSON with TMDB metadata."""

import csv
from typing import Literal, overload

from utils.path_utils import path_from_project_root

from .models import (
    MovieIndex,
    MovieWatchData,
    ShowIndex,
    ShowWatchData,
    WatchedEpisode,
)

SERIES_NAME_COLUMN = "series_name"
MOVIE_NAME_COLUMN = "movie_name"
CREATED_AT_COLUMN = "created_at"
UPDATED_AT_COLUMN = "updated_at"
IS_ARCHIVED_COLUMN = "is_archived"
EPISODE_COUNT_COLUMN = "ep_watch_count"
SHORT_SEASON_COLUMN = "s_no"
SHORT_EPISODE_COLUMN = "ep_no"
SEASON_NUMBER_COLUMN = "season_number"
EPISODE_NUMBER_COLUMN = "episode_number"

# TV Time exports use sortable timestamp strings. These are ordering sentinels,
# not timestamps that should be parsed as dates.
EARLIEST_TIMESTAMP = "0000-00-00 00:00:00"
LATEST_TIMESTAMP = "9999-99-99 99:99:99"


@overload
def create_watch_record(
    media_name: str, media_type: Literal["show"] = "show"
) -> ShowWatchData: ...


@overload
def create_watch_record(
    media_name: str, media_type: Literal["movie"]
) -> MovieWatchData: ...


def create_watch_record(
    media_name: str, media_type: Literal["show", "movie"] = "show"
) -> ShowWatchData | MovieWatchData:
    """Return an initialized watch record for a show or movie."""
    if media_type == "show":
        return {
            "name": media_name,
            # These defaults make overwrite conditions simpler and sorting easier.
            "created_at": LATEST_TIMESTAMP,
            "updated_at": EARLIEST_TIMESTAMP,
            "is_archived": False,
            "total_episodes_watched": 0,
            "episodes_watched": [],
        }
    return {
        "name": media_name,
        "created_at": LATEST_TIMESTAMP,
        "updated_at": EARLIEST_TIMESTAMP,
        "watched": True,
    }


def read_csv_rows(file_path: str) -> list[dict[str, str]]:
    """Return rows from a project-relative CSV file as dictionaries."""
    with open(
        path_from_project_root(file_path), newline="", encoding="utf-8"
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def aggregate_show_data(show_index: ShowIndex, file_path: str) -> ShowIndex:
    """Add show records from a CSV file to ``show_index`` in place."""
    print(f"Running aggregation on file {file_path}")
    csv_rows = read_csv_rows(file_path)

    for csv_row in csv_rows:
        if not csv_row.get(SERIES_NAME_COLUMN):
            continue
        show_name = csv_row[SERIES_NAME_COLUMN].strip()

        if show_name not in show_index:
            show_index[show_name] = create_watch_record(show_name)

        show_data = show_index[show_name]

        if (
            csv_row.get(CREATED_AT_COLUMN)
            and csv_row[CREATED_AT_COLUMN] < show_data["created_at"]
        ):
            show_data["created_at"] = csv_row[CREATED_AT_COLUMN]
            print(f"Updated 'created_at' timestamp for show {show_name}.")

        if (
            csv_row.get(UPDATED_AT_COLUMN)
            and csv_row[UPDATED_AT_COLUMN] >= show_data["updated_at"]
        ):
            if csv_row.get(IS_ARCHIVED_COLUMN):
                previous_archived_value = show_data["is_archived"]
                show_data["is_archived"] = csv_row[
                    IS_ARCHIVED_COLUMN
                ].lower().strip() in [
                    "true",
                    "1",
                ]
                show_data["updated_at"] = csv_row[UPDATED_AT_COLUMN]
                if show_data["is_archived"] != previous_archived_value:
                    print(f"Updated archived status for show {show_name}.")
            if csv_row.get(EPISODE_COUNT_COLUMN):
                previous_episode_count = show_data["total_episodes_watched"]
                show_data["total_episodes_watched"] = max(
                    int(csv_row[EPISODE_COUNT_COLUMN]),
                    show_data["total_episodes_watched"],
                )
                show_data["updated_at"] = csv_row[UPDATED_AT_COLUMN]
                if show_data["total_episodes_watched"] != previous_episode_count:
                    print(f"Updated episode count for show {show_name}.")

        for season_column, episode_column in (
            (SHORT_SEASON_COLUMN, SHORT_EPISODE_COLUMN),
            (SEASON_NUMBER_COLUMN, EPISODE_NUMBER_COLUMN),
        ):
            episode_number = csv_row.get(episode_column)
            if not episode_number:
                continue

            season_number = csv_row.get(season_column)
            watched_entry: WatchedEpisode = {
                "season": int(season_number) if season_number else -1,
                "episode": int(episode_number),
                "updated_at": csv_row[UPDATED_AT_COLUMN],
            }
            if watched_entry not in show_data["episodes_watched"]:
                show_data["episodes_watched"].append(watched_entry)

    return show_index


def aggregate_movie_data(movie_index: MovieIndex, file_path: str) -> MovieIndex:
    """Add movie records from a CSV file to ``movie_index`` in place."""
    print(f"Running aggregation on file {file_path}")
    csv_rows = read_csv_rows(file_path)

    for csv_row in csv_rows:
        if not csv_row.get(MOVIE_NAME_COLUMN):
            continue

        movie_name = csv_row[MOVIE_NAME_COLUMN].strip()

        if movie_name not in movie_index:
            movie_index[movie_name] = create_watch_record(movie_name, "movie")

        movie_data = movie_index[movie_name]

        if csv_row.get(CREATED_AT_COLUMN) and (
            not movie_data["created_at"]
            or csv_row[CREATED_AT_COLUMN] < movie_data["created_at"]
        ):
            movie_data["created_at"] = csv_row[CREATED_AT_COLUMN]

        if (
            csv_row.get(UPDATED_AT_COLUMN)
            and csv_row[UPDATED_AT_COLUMN] >= movie_data["updated_at"]
        ):
            movie_data["updated_at"] = csv_row[UPDATED_AT_COLUMN]

    return movie_index


def sort_episodes_ascending(show_index: ShowIndex) -> None:
    """Sort each episode list in place by season and episode number."""
    print("Sorting episode lists")
    for show_data in show_index.values():
        if show_data.get("episodes_watched"):
            show_data["episodes_watched"].sort(
                key=lambda episode: (episode["season"], episode["episode"])
            )


def deduplicate_show_episodes(shows: list[ShowWatchData]) -> None:
    """Remove duplicate and placeholder episodes from each show."""
    print("Deduplicating episode lists")

    for show_record in shows:
        recorded_episode_count = show_record["total_episodes_watched"]
        watched_episodes = show_record["episodes_watched"]
        unique_episodes = deduplicate_episodes(watched_episodes)

        if unique_episodes != watched_episodes:
            print(f"Removing duplicate episodes for {show_record['name']}")
        show_record["episodes_watched"] = unique_episodes

        if recorded_episode_count != len(unique_episodes):
            print(
                f"Discrepancy for show {show_record['name']}:",
                f"Total watched is {recorded_episode_count} but episode list contains {len(unique_episodes)}.",
            )
            for index, episode in enumerate(unique_episodes, start=1):
                print(f"{index}:", episode)
        print("-")


def deduplicate_episodes(
    episodes_watched: list[WatchedEpisode],
) -> list[WatchedEpisode]:
    """Return the first entry for each season and episode number."""
    seen_episode_keys: set[tuple[int, int]] = set()
    unique_episodes: list[WatchedEpisode] = []
    for episode in episodes_watched:
        episode_key = (episode["season"], episode["episode"])
        if episode_key == (0, 0):
            continue
        if episode_key not in seen_episode_keys:
            seen_episode_keys.add(episode_key)
            unique_episodes.append(episode)
    return unique_episodes
