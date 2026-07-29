import csv
import json
import os
import time
from typing import Literal

import requests

from utils.path_utils import path_from_project_root


def new_watch_data(name: str, type: Literal["show", "movie"] = "show") -> dict:
    data: dict[str, str | bool | list | int] = {
        "name": name,
        # Using these default values (even when they are not valid date-times)
        # makes the overwrite conditions simpler and sorting easier.
        "created_at": "9999-99-99 99:99:99",
        "updated_at": "0000-00-00 00:00:00",
    }
    if type == "show":
        data.update(
            {
                "is_archived": False,
                "total_episodes_watched": 0,
                # A list of dictionaries containing the season, episode and date watched
                "episodes_watched": [],
            }
        )
    elif type == "movie":
        data.update({"watched": True})

    return data


def read_csv_data(file_path):
    """Read a CSV file and return its rows as dictionaries."""
    with open(
        path_from_project_root(file_path), newline="", encoding="utf-8"
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def write_json(data, file_path: str):
    with open(
        path_from_project_root(file_path),
        mode="w",
        encoding="utf-8",
    ) as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)


def aggregate_show_data(aggregated: dict, file_path: str):
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(file_path)

    for entry in raw_watch_data:
        if not entry.get("series_name"):
            continue
        # print("Entry: ", entry)
        show = entry["series_name"].strip()

        if show not in aggregated:
            aggregated[show] = new_watch_data(show)

        show_data: dict = aggregated[show]
        # print(f"Show data before: {show_data}")

        # Update the created_at timestamp with the oldest created_at timestamp found
        if entry.get("created_at") and entry["created_at"] < show_data["created_at"]:
            show_data["created_at"] = entry["created_at"]
            print(f"Updated 'created_at' timestamp for show {show}.")

        # Only update the archived status and number of watched episodes if the
        # entry is more recent
        if entry.get("updated_at") and (entry["updated_at"] >= show_data["updated_at"]):
            if entry.get("is_archived"):
                oldValue = show_data["is_archived"]
                show_data["is_archived"] = entry["is_archived"].lower().strip() in [
                    "true",
                    "1",
                ]
                show_data["updated_at"] = entry["updated_at"]
                if show_data["is_archived"] != oldValue:
                    print(f"Updated archived status for show {show}.")
            if entry.get("ep_watch_count"):
                oldValue = show_data["total_episodes_watched"]
                # Some rows seem to reset values so we'll take the maximum
                show_data["total_episodes_watched"] = max(
                    int(entry["ep_watch_count"]), show_data["total_episodes_watched"]
                )
                show_data["updated_at"] = entry["updated_at"]
                if show_data["total_episodes_watched"] != oldValue:
                    print(f"Updated episode count for show {show}.")

        # For some reason the two season/episode pairs sometimes use different
        # season and episode numbers. For completeness we'll save both if they
        # differ.
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
                # The same episode with a different timestamp is a valid entry
                # since we may rewatch a show.
                watched_entry = {
                    "season": season,
                    "episode": episode,
                    "updated_at": entry["updated_at"],
                }
                if watched_entry not in show_data["episodes_watched"]:
                    show_data["episodes_watched"].append(watched_entry)

        # print(f"Show data after:  {show_data}\n---")
    return aggregated


def aggregate_movie_data(aggregated: dict, file_path: str):
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(file_path)

    for entry in raw_watch_data:
        if not entry.get("movie_name"):
            continue

        movie = entry["movie_name"].strip()

        if movie not in aggregated:
            aggregated[movie] = new_watch_data(movie, "movie")

        movie_data: dict = aggregated[movie]

        if entry.get("created_at") and (
            not movie_data["created_at"]
            or entry["created_at"] < movie_data["created_at"]
        ):
            movie_data["created_at"] = entry["created_at"]

        if entry.get("updated_at") and entry["updated_at"] >= movie_data["updated_at"]:
            movie_data["updated_at"] = entry["updated_at"]

    return aggregated


def sort_episodes_asc(aggregated: dict):
    print("Sorting episode lists")
    for entry in aggregated.values():
        if entry.get("episodes_watched"):
            episodes: list[dict] = entry["episodes_watched"]
            episodes.sort(key=lambda ep: (ep["season"], ep["episode"]))


def fix_episode_list(shows: list[dict]):
    print("Fixing episode lists")

    for show in shows:
        total_watched: int = show["total_episodes_watched"]
        episode_list: list[dict] = show["episodes_watched"]

        if total_watched < len(episode_list):
            print(f"Removing duplicate episodes for {show['name']}")
            show["episodes_watched"] = remove_duplicate_episode(episode_list)
            episode_list = show["episodes_watched"]

        if total_watched != len(show["episodes_watched"]):
            print(
                f"Discrapency for show {show['name']}:",
                f"Total watched is {total_watched} but episode list contains {len(episode_list)}.",
            )
            i = 1
            for ep in episode_list:
                print(f"{i}:", ep)
                i += 1
        print("-")


def remove_duplicate_episode(episodes_watched: list[dict]):
    seen = set()
    episodes = []
    for ep in episodes_watched:
        ep_key = (ep["season"], ep["episode"])
        if ep_key == (0, 0):
            continue
        if ep_key not in seen:
            seen.add(ep_key)
            episodes.append(ep)
    print("Length of new episode list:", len(episodes))
    return episodes


def fetch_tmdb_data(aggregated: dict):
    print("Fetching data")
    api_key = os.getenv("TMDB_TOKEN")
    print(api_key)
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"shows": {}, "movies": {}}

    endpoints = {
        "shows": "https://api.themoviedb.org/3/search/tv",
        "movies": "https://api.themoviedb.org/3/search/movie",
    }

    for media_type, endpoint in endpoints.items():
        for entry in aggregated[media_type]:
            results = []
            page = 1
            total_pages = 1

            print(f"Fetching data for {entry['name']}")
            while page <= total_pages:
                print(f"Fetching page {page}")
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params={"query": entry["name"], "page": page},
                )
                time.sleep(1 / 3)
                response.raise_for_status()

                result = response.json()
                results.extend(result["results"])
                total_pages = result["total_pages"]
                page += 1

            data[media_type][entry["name"]] = results

    return data

# TODO: Create smaller test files to check if the script does what it is
# supposed to.
def main():
    shows = {}
    movies = {}
    aggregated = {"shows": shows, "movies": movies}
    show_files = [
        "tracking-prod-records-v2.csv",
        "show_seen_episode_latest.csv",
        "followed_tv_show.csv",
        "seen_episode_latest.csv",
        "tracking-prod-records.csv",
        "user_tv_show_data.csv",
    ]
    pass_counter = 1
    for file in show_files:
        print(f"=== {pass_counter} ===")
        aggregate_show_data(shows, f"data/tvtime/{file}")
        write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
        pass_counter += 1

    print(f"=== Pass {pass_counter} ===")
    sort_episodes_asc(shows)
    aggregate_movie_data(movies, "data/tvtime/tracking-prod-records.csv")
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print(f"=== Pass {pass_counter} ===")
    print("Flatten dictionary")
    aggregated = {
        # NOTE: The return type of values() is not a normal list and so not
        # serializable to JSON. We must convert it into a list first.
        "shows": list(aggregated["shows"].values()),
        "movies": list(aggregated["movies"].values()),
    }
    pass_counter += 1

    print(f"=== Pass {pass_counter} ===")
    fix_episode_list(aggregated["shows"])
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    write_json(aggregated, "data/tvtime/watch_data_final.json")


if __name__ == "__main__":
    main()
