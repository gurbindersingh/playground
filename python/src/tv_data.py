import csv

from utils.path_utils import path_from_project_root


def read_csv_data(file_path):
    """Read a CSV file and return its rows as dictionaries."""
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def aggregate_watch_data(file_path: str):
    raw_watch_data = read_csv_data(path_from_project_root(file_path))
    aggregated = {}

    for watch_entry in raw_watch_data:
        print(watch_entry)
        show = watch_entry["series_name"]

        if show in aggregated:
            print("update entry")
            episodes_watched = watch_entry["ep_watch_count"]
            episode_number = watch_entry["episode_number"]

            if episodes_watched != "":
                aggregated[show].episodes_watched = int(episodes_watched)
            if episode_number != "":
                aggregated[show].episode_numbers.extend([int(episode_number)])

        else:
            print("create entry")


def main():
    aggregate_watch_data("data/tvtime/tracking-prod-records-v2.csv")


if __name__ == "__main__":
    main()
