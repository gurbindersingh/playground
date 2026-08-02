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


@overload
def new_watch_data(name: str, type: Literal["show"] = "show") -> ShowWatchData: ...


@overload
def new_watch_data(name: str, type: Literal["movie"]) -> MovieWatchData: ...


def new_watch_data(
    name: str, type: Literal["show", "movie"] = "show"
) -> ShowWatchData | MovieWatchData:
    """Return an initialized watch record for a show or movie."""
    if type == "show":
        return {
            "name": name,
            # These defaults make overwrite conditions simpler and sorting easier.
            "created_at": "9999-99-99 99:99:99",
            "updated_at": "0000-00-00 00:00:00",
            "is_archived": False,
            "total_episodes_watched": 0,
            "episodes_watched": [],
        }
    return {
        "name": name,
        "created_at": "9999-99-99 99:99:99",
        "updated_at": "0000-00-00 00:00:00",
        "watched": True,
    }


def read_csv_data(file_path: str) -> list[dict[str, str]]:
    """Return rows from a project-relative CSV file as dictionaries."""
    with open(
        path_from_project_root(file_path), newline="", encoding="utf-8"
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def aggregate_show_data(aggregated: ShowIndex, file_path: str) -> ShowIndex:
    """Add show records from a CSV file to ``aggregated`` in place."""
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(file_path)

    for entry in raw_watch_data:
        if not entry.get("series_name"):
            continue
        show = entry["series_name"].strip()

        if show not in aggregated:
            aggregated[show] = new_watch_data(show)

        show_data = aggregated[show]

        if entry.get("created_at") and entry["created_at"] < show_data["created_at"]:
            show_data["created_at"] = entry["created_at"]
            print(f"Updated 'created_at' timestamp for show {show}.")

        if entry.get("updated_at") and entry["updated_at"] >= show_data["updated_at"]:
            if entry.get("is_archived"):
                old_value = show_data["is_archived"]
                show_data["is_archived"] = entry["is_archived"].lower().strip() in [
                    "true",
                    "1",
                ]
                show_data["updated_at"] = entry["updated_at"]
                if show_data["is_archived"] != old_value:
                    print(f"Updated archived status for show {show}.")
            if entry.get("ep_watch_count"):
                old_value = show_data["total_episodes_watched"]
                show_data["total_episodes_watched"] = max(
                    int(entry["ep_watch_count"]), show_data["total_episodes_watched"]
                )
                show_data["updated_at"] = entry["updated_at"]
                if show_data["total_episodes_watched"] != old_value:
                    print(f"Updated episode count for show {show}.")

        episode_pairs = [
            (
                int(entry["s_no"]) if entry.get("s_no") else -1,
                int(entry["ep_no"]) if entry.get("ep_no") else None,
            ),
        ]
        alternate_pair = (
            int(entry["season_number"]) if entry.get("season_number") else -1,
            int(entry["episode_number"]) if entry.get("episode_number") else None,
        )
        if alternate_pair != episode_pairs[0]:
            episode_pairs.append(alternate_pair)

        for season, episode in episode_pairs:
            if episode is not None:
                watched_entry: WatchedEpisode = {
                    "season": season,
                    "episode": episode,
                    "updated_at": entry["updated_at"],
                }
                if watched_entry not in show_data["episodes_watched"]:
                    show_data["episodes_watched"].append(watched_entry)

    return aggregated


def aggregate_movie_data(aggregated: MovieIndex, file_path: str) -> MovieIndex:
    """Add movie records from a CSV file to ``aggregated`` in place."""
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(file_path)

    for entry in raw_watch_data:
        if not entry.get("movie_name"):
            continue

        movie = entry["movie_name"].strip()

        if movie not in aggregated:
            aggregated[movie] = new_watch_data(movie, "movie")

        movie_data = aggregated[movie]

        if entry.get("created_at") and (
            not movie_data["created_at"]
            or entry["created_at"] < movie_data["created_at"]
        ):
            movie_data["created_at"] = entry["created_at"]

        if entry.get("updated_at") and entry["updated_at"] >= movie_data["updated_at"]:
            movie_data["updated_at"] = entry["updated_at"]

    return aggregated


def sort_episodes_asc(aggregated: ShowIndex) -> None:
    """Sort each episode list in place by season and episode number."""
    print("Sorting episode lists")
    for entry in aggregated.values():
        if entry.get("episodes_watched"):
            entry["episodes_watched"].sort(
                key=lambda episode: (episode["season"], episode["episode"])
            )


def dedupe_episode_list(shows: list[ShowWatchData]) -> None:
    """Remove duplicate episodes when a list exceeds its recorded total."""
    print("Depuplicating episode lists")

    for show in shows:
        total_watched = show["total_episodes_watched"]
        episode_list = show["episodes_watched"]

        if total_watched < len(episode_list):
            print(f"Removing duplicate episodes for {show['name']}")
            show["episodes_watched"] = remove_duplicate_episode(episode_list)
            episode_list = show["episodes_watched"]

        if total_watched != len(show["episodes_watched"]):
            print(
                f"Discrapency for show {show['name']}:",
                f"Total watched is {total_watched} but episode list contains {len(episode_list)}.",
            )
            for index, episode in enumerate(episode_list, start=1):
                print(f"{index}:", episode)
        print("-")


def remove_duplicate_episode(
    episodes_watched: list[WatchedEpisode],
) -> list[WatchedEpisode]:
    """Return the first entry for each season and episode number."""
    seen: set[tuple[int, int]] = set()
    episodes: list[WatchedEpisode] = []
    for episode in episodes_watched:
        episode_key = (episode["season"], episode["episode"])
        if episode_key == (0, 0):
            continue
        if episode_key not in seen:
            seen.add(episode_key)
            episodes.append(episode)
    print("Length of new episode list:", len(episodes))
    return episodes
