import csv
import json

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
        json.dump(data, json_file, indent=2)


def aggregate_watch_data(aggregated, file_path: str):
    print(f"Running aggregation on file {file_path}")
    raw_watch_data = read_csv_data(path_from_project_root(file_path))

    for entry in raw_watch_data:
        if not entry["series_name"]:
            continue
        # print("Entry: ", entry)
        show = entry["series_name"].strip()

        if show not in aggregated:
            aggregated[show] = new_show(show)

        show_data = aggregated[show]
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
                show_data["total_episodes_watched"] = int(entry["ep_watch_count"])
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
                # The same episode with a different timestamp is a valid entry since we may rewatch a show.
                watched_entry = {
                    "season": season,
                    "episode": episode,
                    "updated_at": entry["updated_at"],
                }
                if watched_entry not in show_data["episodes_watched"]:
                    show_data["episodes_watched"].append(watched_entry)

        # print(f"Show data after:  {show_data}\n---")
    return aggregated


# TODO: Create smaller test files to check if the script does what it is
# supposed to.
def main():
    aggregated = {}
    print("=== Pass 1 ===")
    aggregate_watch_data(aggregated, "data/tvtime/tracking-prod-records-v2.csv")
    write_json(aggregated, "data/tvtime/watch_data_1.json")
    print("=== Pass 2 ===")
    aggregate_watch_data(aggregated, "data/tvtime/show_seen_episode_latest.csv")
    write_json(aggregated, "data/tvtime/watch_data_2.json")
    print("=== Pass 3 ===")
    aggregate_watch_data(aggregated, "data/tvtime/followed_tv_show.csv")
    write_json(aggregated, "data/tvtime/watch_data_3.json")
    print("=== Pass 4 ===")


if __name__ == "__main__":
    main()
