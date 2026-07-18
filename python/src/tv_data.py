import csv
import json
from datetime import datetime, timezone
from typing import Dict

from utils.path_utils import path_from_project_root


def new_show(name):
    return {
        "name": name,
        "type": "show",
        "total_episodes_watched": -1,
        "is_archived": False,
        "created_at": "",
        "updated_at": "0000-00-00 00:00:00",
        # A list of dictionaries containing the season, episode and date watched
        "episodes_watched": [],
    }


def read_csv_data(file_path):
    """Read a CSV file and return its rows as dictionaries."""
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_json(data, file_path: str):
    with open(
        path_from_project_root(file_path),
        mode="w",
        encoding="utf-8",
    ) as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)


def aggregate_show_data(aggregated: Dict, file_path: str):
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(path_from_project_root(file_path))

    for entry in raw_watch_data:
        if not entry.get("series_name"):
            continue
        # print("Entry: ", entry)
        show = entry["series_name"].strip()

        if show not in aggregated:
            aggregated[show] = new_show(show)

        show_data: Dict = aggregated[show]
        # print(f"Show data before: {show_data}")

        # Update the created_at timestamp only it is empty or if the new
        # timestamp is older.
        if entry.get("created_at") and (
            not show_data["created_at"] or entry["created_at"] < show_data["created_at"]
        ):
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
                    # The show name is here so that when we run a diff tool, we
                    # can actually see for what show the episodes were
                    # modified.
                    "show": show,
                }
                if watched_entry not in show_data["episodes_watched"]:
                    show_data["episodes_watched"].append(watched_entry)

        # print(f"Show data after:  {show_data}\n---")
    return aggregated


def aggregate_movie_data(aggregated: Dict, file_path: str):
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(path_from_project_root(file_path))

    for entry in raw_watch_data:
        if not entry.get("movie_name"):
            continue

        movie = entry["movie_name"].strip()

        if movie not in aggregated:
            aggregated[movie] = {
                "name": movie,
                "type": "movie",
                "created_at": "",
                "updated_at": "0000-00-00 00:00:00",
            }

        movie_data: Dict = aggregated[movie]

        if entry.get("created_at") and (
            not movie_data["created_at"]
            or entry["created_at"] < movie_data["created_at"]
        ):
            movie_data["created_at"] = entry["created_at"]

        if entry.get("updated_at") and entry["updated_at"] >= movie_data["updated_at"]:
            movie_data["updated_at"] = entry["updated_at"]

    return aggregated


# TODO: Create smaller test files to check if the script does what it is
# supposed to.
def main():
    aggregated = {}
    print("=== Pass 1 ===")
    aggregate_show_data(aggregated, "data/tvtime/tracking-prod-records-v2.csv")
    write_json(aggregated, "data/tvtime/watch_data_1.json")
    print("=== Pass 2 ===")
    aggregate_show_data(aggregated, "data/tvtime/show_seen_episode_latest.csv")
    write_json(aggregated, "data/tvtime/watch_data_2.json")
    print("=== Pass 3 ===")
    aggregate_show_data(aggregated, "data/tvtime/followed_tv_show.csv")
    write_json(aggregated, "data/tvtime/watch_data_3.json")
    print("=== Pass 4 ===")
    aggregate_show_data(aggregated, "data/tvtime/seen_episode_latest.csv")
    write_json(aggregated, "data/tvtime/watch_data_4.json")
    print("=== Pass 5 ===")
    aggregate_show_data(aggregated, "data/tvtime/tracking-prod-records.csv")
    write_json(aggregated, "data/tvtime/watch_data_5.json")
    print("=== Pass 6 ===")
    aggregate_movie_data(aggregated, "data/tvtime/tracking-prod-records.csv")
    write_json(aggregated, "data/tvtime/watch_data_6.json")
    print("=== Pass 7 ===")
    aggregate_show_data(aggregated, "data/tvtime/user_tv_show_data.csv")
    write_json(aggregated, "data/tvtime/watch_data_7.json")
    write_json(aggregated, "data/tvtime/watch_data_final.json")


if __name__ == "__main__":
    main()
