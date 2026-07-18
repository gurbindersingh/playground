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


def aggregate_watch_data(file_path: str):
    raw_watch_data = read_csv_data(path_from_project_root(file_path))
    aggregated = {}

    for entry in raw_watch_data:
        print("Entry: ", entry)
        show = entry["series_name"]

        if show not in aggregated:
            aggregated[show] = new_show(show)

        show_data = aggregated[show]
        print(f"Show data before: {show_data}")

        # Update the created_at timestamp only it is empty or if the new
        # timestamp is older.
        if entry["created_at"] and (
            not show_data["created_at"] or entry["created_at"] < show_data["created_at"]
        ):
            show_data["created_at"] = entry["created_at"]

        # Only update the archived status and number of watched episodes if the
        # entry is more recent
        if entry["updated_at"] and (entry["updated_at"] >= show_data["updated_at"]):
            if entry["is_archived"]:
                show_data["is_archived"] = entry["is_archived"] == "true"
                show_data["updated_at"] = entry["updated_at"]
            if entry["ep_watch_count"]:
                show_data["total_episodes_watched"] = max(
                    show_data["total_episodes_watched"], int(entry["ep_watch_count"])
                )
                show_data["updated_at"] = entry["updated_at"]

        # For some reason the two season/episode pairs sometimes use different
        # season and episode numbers. For completeness we'll save both if they
        # differ.
        episode_pairs = [
            (entry["s_no"], entry["ep_no"]),
        ]
        alternate_pair = (
            entry["season_number"],
            entry["episode_number"],
        )
        if alternate_pair != episode_pairs[0]:
            episode_pairs.append(alternate_pair)

        for season, episode in episode_pairs:
            if season and episode:
                show_data["episodes_watched"].append(
                    {
                        "season": int(season),
                        "episode": int(episode),
                        "updated_at": entry["updated_at"],
                    }
                )

        print(f"Show data after:  {show_data}")
        print("---")
    return aggregated


def aggregate_follow_status(aggregated, file_path: str):
    raw_follow_data = read_csv_data(path_from_project_root(file_path))

    for follow_entry in raw_follow_data:
        # print(follow_entry)
        show = follow_entry["tv_show_name"]
        archived = follow_entry["archived"]
        if show not in aggregated:
            print(f"Show {show} not in aggregated data.")
            aggregated[show] = new_show(show)
        updated_at = follow_entry["updated_at"]
        if updated_at > aggregated[show]["updated_at"]:
            aggregated[show]["updated_at"] = updated_at
            if archived:
                aggregated[show]["is_archived"] = archived == "1"


def aggregate_episode_and_follow_status(aggregated, file_path: str):
    raw_data = read_csv_data(path_from_project_root(file_path))

    for entry in raw_data:
        print(entry)
        show = entry["tv_show_name"]
        episodes_seen = entry["nb_episodes_seen"]
        updated_at = entry.get("updated_at", "")

        if show not in aggregated:
            print(f"Show {show} not in aggregated data.")
            aggregated[show] = new_show(show)

        is_newer_update = updated_at > aggregated[show]["updated_at"]
        if is_newer_update:
            aggregated[show]["updated_at"] = updated_at
        if episodes_seen:
            aggregated[show]["total_episodes_watched"] = max(
                int(episodes_seen), aggregated[show]["total_episodes_watched"]
            )
        print(aggregated[show])


def main():
    aggregated = aggregate_watch_data("data/tvtime/tracking-prod-records-v2.csv")
    write_json(aggregated, "data/tvtime/watch_data.json")
    aggregate_follow_status(aggregated, "data/tvtime/followed_tv_show.csv")
    write_json(aggregated, "data/tvtime/watch_data_2.json")
    aggregate_episode_and_follow_status(aggregated, "data/tvtime/user_tv_show_data.csv")
    write_json(aggregated, "data/tvtime/watch_data_3.json")


if __name__ == "__main__":
    main()
