import csv
import json

from utils.path_utils import path_from_project_root


def new_show(name):
    return {
        "show": name,
        "total_episodes_watched": -1,
        # A list of dictionaries containing the season, episode and date watched
        "episodes_watched": [],
        "is_archived": False,
        "created_at": "0000-01-01 00:00",
        "updated_at": "0000-01-01 00:00",
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

    for watch_entry in raw_watch_data:
        print(watch_entry)
        show = watch_entry["series_name"]

        if show not in aggregated:
            aggregated[show] = new_show(show)

        show_data = aggregated[show]
        # If the created_at entry exists and is non-empty
        if watch_entry["created_at"] and show_data["created_at"] == "0000-01-01 00:00":
            show_data["created_at"] = watch_entry["created_at"]

        if watch_entry["updated_at"] > show_data["updated_at"]:
            show_data["updated_at"] = watch_entry["updated_at"]
            if watch_entry["is_archived"]:
                show_data["is_archived"] = watch_entry["is_archived"] == "true"

        if watch_entry["ep_watch_count"]:
            show_data["total_episodes_watched"] = max(
                show_data["total_episodes_watched"], int(watch_entry["ep_watch_count"])
            )

        episode_pairs = [
            (watch_entry["s_no"], watch_entry["ep_no"]),
        ]
        alternate_pair = (
            watch_entry["season_number"],
            watch_entry["episode_number"],
        )
        if alternate_pair != episode_pairs[0]:
            episode_pairs.append(alternate_pair)

        for season, episode in episode_pairs:
            if season and episode:
                show_data["episodes_watched"].append(
                    {
                        "season": int(season),
                        "episode": int(episode),
                        "updated_at": watch_entry["updated_at"],
                    }
                )

        print(show_data)
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
