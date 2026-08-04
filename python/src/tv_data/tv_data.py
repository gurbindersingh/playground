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
    """Create the initial mutable record used while combining CSV rows.

    ``media_name`` is the already-trimmed TV Time title. Shows start with an
    empty watched-episode list and an active archive state; movies imported from
    TV Time start as watched. Sentinel timestamps allow aggregation to replace
    them with the earliest creation and latest relevant update strings.
    """
    if media_type == "show":
        return {
            "name": media_name,
            # These defaults make overwrite conditions simpler and sorting easier.
            "created_at": LATEST_TIMESTAMP,
            "updated_at": EARLIEST_TIMESTAMP,
            "is_archived": False,
            "episodes_watched": [],
        }
    return {
        "name": media_name,
        "created_at": LATEST_TIMESTAMP,
        "updated_at": EARLIEST_TIMESTAMP,
        "watched": True,
    }


def read_csv_rows(file_path: str) -> list[dict[str, str]]:
    """Read an entire project-relative CSV file into row dictionaries.

    Dictionary keys normally come from the header row and populated values are
    strings because later aggregation decides how each column is interpreted.
    Irregular rows can contain ``None`` for missing cells or a ``None`` key for
    surplus cells. The file is opened as UTF-8 with CSV newline handling. File,
    decoding, and CSV parsing errors are passed to the caller.
    """
    with open(
        path_from_project_root(file_path), newline="", encoding="utf-8"
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def aggregate_show_data(show_index: ShowIndex, file_path: str) -> ShowIndex:
    """Merge one TV Time show export into an existing title index.

    The supplied ``show_index`` is mutated and returned for convenient chaining.
    Rows with blank names are reported and skipped. For each show, aggregation
    keeps the earliest creation timestamp, and collects episodes from both TV
    Time column naming formats. A truthy raw archive value on a row at least as
    new as the stored update changes archive status; only ``"true"`` and ``"1"``
    mean archived. Episode numbers are converted to integers, and a missing
    season is stored as ``-1``. Invalid numbers or a missing ``updated_at`` key
    for an imported episode raise normal conversion or key errors; blank cell
    values are not validated.

    Progress and changed metadata are printed to standard output.
    """
    print(f"Running aggregation on file {file_path}")
    csv_rows = read_csv_rows(file_path)

    for row_number, csv_row in enumerate(csv_rows, start=2):
        show_name = (csv_row.get(SERIES_NAME_COLUMN) or "").strip()
        if not show_name:
            print(f"Skipping blank show name in {file_path} at CSV row {row_number}.")
            continue

        if show_name not in show_index:
            show_index[show_name] = create_watch_record(show_name)

        show_data = show_index[show_name]
        created_at = csv_row.get(CREATED_AT_COLUMN)
        updated_at = csv_row.get(UPDATED_AT_COLUMN)
        archived_value = csv_row.get(IS_ARCHIVED_COLUMN)

        if created_at and created_at < show_data["created_at"]:
            show_data["created_at"] = created_at
            print(f"Updated 'created_at' timestamp for show {show_name}.")

        if updated_at and updated_at >= show_data["updated_at"]:
            if archived_value:
                previous_archived_value = show_data["is_archived"]
                show_data["is_archived"] = archived_value.lower().strip() in [
                    "true",
                    "1",
                ]
                if show_data["is_archived"] != previous_archived_value:
                    print(f"Updated archived status for show {show_name}.")
            if archived_value:
                show_data["updated_at"] = updated_at

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
    """Merge one TV Time movie export into an existing title index.

    The supplied ``movie_index`` is mutated and returned. Blank names are
    reported and skipped. Repeated movie rows keep the earliest creation string
    and latest update string, and every imported movie remains marked watched.
    Reading errors are passed through from :func:`read_csv_rows`.
    """
    print(f"Running aggregation on file {file_path}")
    csv_rows = read_csv_rows(file_path)

    for row_number, csv_row in enumerate(csv_rows, start=2):
        movie_name = (csv_row.get(MOVIE_NAME_COLUMN) or "").strip()
        if not movie_name:
            print(f"Skipping blank movie name in {file_path} at CSV row {row_number}.")
            continue

        if movie_name not in movie_index:
            movie_index[movie_name] = create_watch_record(movie_name, "movie")

        movie_data = movie_index[movie_name]
        created_at = csv_row.get(CREATED_AT_COLUMN)
        updated_at = csv_row.get(UPDATED_AT_COLUMN)

        if created_at and created_at < movie_data["created_at"]:
            movie_data["created_at"] = created_at

        if updated_at and updated_at >= movie_data["updated_at"]:
            movie_data["updated_at"] = updated_at

    return movie_index


def sort_episodes_ascending(show_index: ShowIndex) -> None:
    """Sort every indexed show's watched episodes in place.

    Ordering is numeric by season first and episode second. The function returns
    nothing and prints a progress message; show records and episode objects are
    otherwise unchanged.
    """
    print("Sorting episode lists")
    for show_data in show_index.values():
        show_data["episodes_watched"].sort(
            key=lambda episode: (episode["season"], episode["episode"])
        )


def deduplicate_show_episodes(shows: list[ShowWatchData]) -> None:
    """Replace each show's episode list with its cleaned equivalent.

    Cleaning delegates to :func:`deduplicate_episodes`, so duplicate episode
    keys retain their newest update and the ``(0, 0)`` placeholder is removed.
    The supplied show records are mutated. A message is printed when a list
    changes.
    """
    print("Deduplicating episode lists")

    for show_record in shows:
        watched_episodes = show_record["episodes_watched"]
        unique_episodes = deduplicate_episodes(watched_episodes)

        if unique_episodes != watched_episodes:
            print(f"Removing duplicate episodes for {show_record['name']}")
            print("-")
        show_record["episodes_watched"] = unique_episodes


def deduplicate_episodes(
    episodes_watched: list[WatchedEpisode],
) -> list[WatchedEpisode]:
    """Build a cleaned, ordered episode list without mutating the input.

    Episodes are identified by their ``(season, episode)`` pair. The entry with
    the greatest sortable ``updated_at`` string survives when the pair appears
    more than once. Equal timestamps retain the first encountered entry.
    ``(0, 0)`` is discarded as an export placeholder, and the returned list is
    ordered by season and episode number.
    """
    newest_episodes: dict[tuple[int, int], WatchedEpisode] = {}
    for episode in episodes_watched:
        episode_key = (episode["season"], episode["episode"])
        if episode_key == (0, 0):
            continue
        existing_episode = newest_episodes.get(episode_key)
        if (
            existing_episode is None
            or episode["updated_at"] > existing_episode["updated_at"]
        ):
            newest_episodes[episode_key] = episode

    return [newest_episodes[key] for key in sorted(newest_episodes)]
