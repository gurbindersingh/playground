import csv
import json

from utils.path_utils import path_from_project_root


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
        episodes_watched = watch_entry["ep_watch_count"]
        episode_number = watch_entry["episode_number"]
        is_archived = watch_entry["is_archived"]

        if show not in aggregated:
            aggregated[show] = {
                "show": show,
                "episodes_watched": -1,
                "episode_numbers": [],
            }
        aggregated[show]["is_archived"] = is_archived != "" and is_archived == "true"
        if episodes_watched != "":
            aggregated[show]["episodes_watched"] = int(episodes_watched)
        if episode_number != "":
            aggregated[show]["episode_numbers"].extend([int(episode_number)])

        print(aggregated[show])
    return aggregated


def aggregate_follow_status(aggregated, file_path: str):
    raw_follow_data = read_csv_data(file_path)

    for follow_entry in raw_follow_data:
        print(follow_entry)
        show = follow_entry["tv_show_name"]
        archived = follow_entry["archived"]
        aggregated[show]["is_archived"] = archived == "1"


def main():
    aggregated = aggregate_watch_data("data/tvtime/tracking-prod-records-v2.csv")
    write_json(aggregated, "data/tvtime/watch_data.json")
    aggregate_follow_status(aggregated, "data/tvtime/followed_tv_show.csv")
    write_json(aggregated, "data/tvtime/watch_data_2.json")


if __name__ == "__main__":
    main()
