import csv
import json
import os
import re
import time
from typing import Literal

import requests

from utils.path_utils import path_from_project_root

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_DETAILS_CACHE_PATH = "data/tvtime/tmdb_details.json"
TMDB_REQUEST_TIMEOUT = 30
TMDB_REQUEST_INTERVAL = 1 / 3

SHOW_SCALAR_FIELDS = (
    "first_air_date",
    "last_air_date",
    "homepage",
    "id",
    "in_production",
    "next_episode_to_air",
    "original_name",
    "backdrop_path",
    "poster_path",
    "number_of_episodes",
    "number_of_seasons",
    "overview",
    "popularity",
    "status",
    "type",
    "vote_average",
    "vote_count",
)
SHOW_LIST_FIELDS = ("genres", "languages", "seasons")
MOVIE_SCALAR_FIELDS = (
    "release_date",
    "homepage",
    "id",
    "original_language",
    "original_title",
    "title",
    "backdrop_path",
    "poster_path",
    "overview",
    "popularity",
    "runtime",
    "status",
    "vote_average",
    "vote_count",
)
MOVIE_LIST_FIELDS = ("genres", "spoken_languages")
EPISODE_METADATA_FIELDS = (
    "name",
    "overview",
    "air_date",
    "runtime",
    "still_path",
    "vote_average",
    "vote_count",
)


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


def read_json(file_path: str) -> dict:
    """Read a JSON file and return as a dictionary."""
    with open(
        path_from_project_root(file_path), mode="r", encoding="utf-8"
    ) as json_file:
        return json.load(json_file)


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


def dedupe_episode_list(shows: list[dict]):
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


def tmdb_lookup_title_and_year(name: str) -> tuple[str, str | None]:
    match = re.fullmatch(r"(.+) \((\d{4})\)", name)
    if match:
        return match.group(1), match.group(2)
    return name, None


def fetch_tmdb_data(aggregated: dict):
    print("Fetching data")
    api_key = os.getenv("TMDB_TOKEN")
    if not api_key:
        raise RuntimeError("TMDB_TOKEN is required to fetch TMDB data.")
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"shows": {}, "movies": {}}

    endpoints = {
        "shows": f"{TMDB_API_BASE_URL}/search/tv",
        "movies": f"{TMDB_API_BASE_URL}/search/movie",
    }

    for media_type, endpoint in endpoints.items():
        for entry in aggregated[media_type]:
            results = []
            page = 1
            total_pages = 1
            query_name, _ = tmdb_lookup_title_and_year(entry["name"])

            print(f"Fetching data for {entry['name']}")
            while page <= total_pages:
                print(f"Fetching page {page}")
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params={"query": query_name, "page": page},
                    timeout=TMDB_REQUEST_TIMEOUT,
                )
                time.sleep(TMDB_REQUEST_INTERVAL)
                response.raise_for_status()

                result = response.json()
                results.extend(result["results"])
                total_pages = result["total_pages"]
                page += 1

            data[media_type][entry["name"]] = results

    return data


def selected_tmdb_id(results: object) -> int | None:
    if not isinstance(results, list) or len(results) != 1:
        return None

    candidate = results[0]
    if not isinstance(candidate, dict):
        return None

    tmdb_id = candidate.get("id")
    return tmdb_id if type(tmdb_id) is int else None


def is_valid_tmdb_detail(detail: object, tmdb_id: int) -> bool:
    return isinstance(detail, dict) and detail.get("id") == tmdb_id


def fetch_details(tmdb_data: dict, cached_details: dict) -> tuple[dict, list[str]]:
    details = dict(cached_details) if isinstance(cached_details, dict) else {}
    for media_type in ("shows", "movies"):
        if not isinstance(details.get(media_type), dict):
            details[media_type] = {}

    endpoints = {
        "shows": f"{TMDB_API_BASE_URL}/tv",
        "movies": f"{TMDB_API_BASE_URL}/movie",
    }
    api_key = os.getenv("TMDB_TOKEN")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    failures = []
    attempted_ids: set[tuple[str, int]] = set()
    total_entries = sum(len(tmdb_data.get(media_type, {})) for media_type in endpoints)
    cached_count = 0
    fetched_count = 0
    unresolved_count = 0
    progress = 0
    request_count = 0

    for media_type in ("shows", "movies"):
        for migration_name, results in tmdb_data.get(media_type, {}).items():
            progress += 1
            progress_prefix = (
                f"[{progress}/{total_entries}] {media_type[:-1].title()}: "
            )
            tmdb_id = selected_tmdb_id(results)
            if tmdb_id is None:
                print(f"{progress_prefix}{migration_name} (no selected ID)")
                unresolved_count += 1
                continue

            detail_cache = details[media_type]
            cache_key = str(tmdb_id)
            if is_valid_tmdb_detail(detail_cache.get(cache_key), tmdb_id):
                print(f"{progress_prefix}{migration_name} (cached)")
                cached_count += 1
                continue

            request_key = (media_type, tmdb_id)
            if request_key in attempted_ids:
                print(f"{progress_prefix}{migration_name} (previous request failed)")
                continue
            attempted_ids.add(request_key)

            if headers is None:
                print(f"{progress_prefix}{migration_name} (failed)")
                failures.append(
                    f"Cannot fetch {media_type[:-1]} {migration_name} ({tmdb_id}): "
                    "TMDB_TOKEN is not set."
                )
                continue

            print(f"{progress_prefix}{migration_name} (fetching)")
            try:
                response = requests.get(
                    f"{endpoints[media_type]}/{tmdb_id}",
                    headers=headers,
                    timeout=TMDB_REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                detail = response.json()
                if not is_valid_tmdb_detail(detail, tmdb_id):
                    raise ValueError(
                        "TMDB detail response has an invalid or mismatched ID."
                    )
            except (requests.RequestException, ValueError) as error:
                failures.append(
                    f"Could not fetch {media_type[:-1]} {migration_name} ({tmdb_id}): "
                    f"{error}"
                )
            else:
                detail_cache[cache_key] = detail
                fetched_count += 1
            finally:
                time.sleep(TMDB_REQUEST_INTERVAL)
                request_count += 1
                if request_count % 5 == 0:
                    write_json(details, TMDB_DETAILS_CACHE_PATH)
                    print(f"Saved TMDB detail cache after {request_count} requests.")

    print(
        "TMDB details: "
        f"{cached_count} cached, {fetched_count} fetched, "
        f"{unresolved_count} unresolved, {len(failures)} failed"
    )
    return details, failures


def add_metadata_defaults(
    entry: dict, scalar_fields: tuple[str, ...], list_fields: tuple[str, ...]
):
    for field in scalar_fields:
        entry.setdefault(field, None)
    for field in list_fields:
        entry.setdefault(field, [])


def enrich_data(aggregated: dict, tmdb_data: dict, tmdb_details: dict):
    media_types = (
        ("shows", SHOW_SCALAR_FIELDS, SHOW_LIST_FIELDS),
        ("movies", MOVIE_SCALAR_FIELDS, MOVIE_LIST_FIELDS),
    )

    for media_type, scalar_fields, list_fields in media_types:
        for entry in aggregated[media_type]:
            migration_name = entry["name"]
            add_metadata_defaults(entry, scalar_fields, list_fields)

            if media_type == "shows":
                for episode in entry.get("episodes_watched", []):
                    for field in EPISODE_METADATA_FIELDS:
                        episode.setdefault(field, None)

            tmdb_id = selected_tmdb_id(
                tmdb_data.get(media_type, {}).get(migration_name)
            )
            if tmdb_id is None:
                continue

            detail = tmdb_details.get(media_type, {}).get(str(tmdb_id))
            if not is_valid_tmdb_detail(detail, tmdb_id):
                raise RuntimeError(
                    f"Missing cached TMDB detail for {media_type[:-1]} "
                    f"{migration_name} ({tmdb_id})."
                )

            for field in (*scalar_fields, *list_fields):
                if field in detail:
                    entry[field] = detail[field]

            if media_type == "shows":
                canonical_name = detail.get("name")
                if isinstance(canonical_name, str) and canonical_name.strip():
                    entry["name"] = canonical_name
            else:
                canonical_title = detail.get("title")
                if isinstance(canonical_title, str) and canonical_title.strip():
                    entry["name"] = canonical_title
                    entry["title"] = canonical_title


def refetch_empty_tmdb_data(aggregated: dict, tmdb_data: dict):
    retry_data = {"shows": [], "movies": []}

    for media_type in ("shows", "movies"):
        for entity_name, tmdb_results in list(tmdb_data[media_type].items()):
            if tmdb_results:
                continue

            # Check if the name also appears in the aggregated data to catch
            # any deviations, e.g. due to manual editing.
            matches_in_aggregated = [
                entry
                for entry in aggregated[media_type]
                if entry["name"] == entity_name
            ]
            if not matches_in_aggregated:
                # Aggregated data does not contain the entity_name name. This
                # should never actually be case but if does we don't overwrite
                # the TMDB entry.
                print(
                    f"No aggregated {media_type[:-1]} entry for empty TMDB result "
                    f"{entity_name}."
                )
                continue
            if len(matches_in_aggregated) > 1:
                # There really shouldn't be multiple entries. But just in case.
                print(f"{entity_name} has multiple entries in aggregated data.")
                continue

            retry_data[media_type].append(matches_in_aggregated[0])

    if not retry_data["shows"] and not retry_data["movies"]:
        return

    # Fetch only the entries that were empty in the saved TMDB data.
    refetched_data = fetch_tmdb_data(retry_data)
    for media_type in ("shows", "movies"):
        # Replace the original empty lists without changing their dictionary keys.
        tmdb_data[media_type].update(refetched_data[media_type])


def filter_tmdb_candidates(
    results: list[dict],
    entity_title: str,
    title_field: str,
    release_date_field: str,
    cached_id: int | None,
) -> list[dict]:
    if len(results) <= 1:
        return results

    cached_matches = [match for match in results if match.get("id") == cached_id]
    if cached_matches:
        return cached_matches

    lookup_title, lookup_year = tmdb_lookup_title_and_year(entity_title)
    title_matches = [
        match for match in results if match.get(title_field) == lookup_title
    ]
    year_matches = [
        match
        for match in title_matches
        if lookup_year and (match.get(release_date_field) or "").startswith(lookup_year)
    ]
    return year_matches or title_matches or results


def choose_tmdb_match(
    entity_title: str,
    media_type: str,
    results: list[dict],
    title_field: str,
    original_title_field: str,
    release_date_field: str,
) -> dict | None:
    print(f"\n\n\nMultiple {media_type[:-1]} matches for {entity_title}:")
    for index, match in enumerate(results, start=1):
        release_date = match.get(release_date_field)
        tmdb_id = match.get("id")
        print(f"{index}.")
        print("-----")
        print(
            f"{match.get(title_field) or '<Unknown>'} | "
            f"{match.get(original_title_field) or '<Unknown>'} | "
            f"{release_date or '<Unknown>'} | "
            f"{tmdb_id if tmdb_id is not None else '<Unknown>'}"
        )
        print(f"Description: {match.get('overview') or '<Unknown>'}")
        print("-----")

    while True:
        choice = input(
            "Choose a match by number, or type s/skip to leave unresolved: "
        ).strip()
        if choice.lower() in ("s", "skip"):
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(results):
            return results[int(choice) - 1]
        print(f"Enter a number from 1 to {len(results)}.")


def filter_tmdb_data(data: dict):
    # Cache selection so we don't have to redo them on every run of the program.
    cache_file_path = "data/tvtime/tmdb_selection_cache.json"
    if os.path.exists(path_from_project_root(cache_file_path)):
        selection_cache = read_json(cache_file_path)
    else:
        selection_cache = {"shows": {}, "movies": {}}

    media_types = (
        ("shows", "name", "original_name", "first_air_date"),
        ("movies", "title", "original_title", "release_date"),
    )
    no_match_count = 0
    multiple_match_count = 0

    for media_type, title_field, _, release_date_field in media_types:
        for entity_title, results in data[media_type].items():
            data[media_type][entity_title] = filter_tmdb_candidates(
                results,
                entity_title,
                title_field,
                release_date_field,
                selection_cache[media_type].get(entity_title),
            )
            filtered_results = data[media_type][entity_title]

            if not filtered_results:
                print(f"No exact {media_type[:-1]} match for {entity_title}.")
                no_match_count += 1
            elif len(filtered_results) > 1:
                multiple_match_count += 1

    print(f"Entries with no matches: {no_match_count}")
    print(f"Entries with multiple matches: {multiple_match_count}")

    for (
        media_type,
        title_field,
        original_title_field,
        release_date_field,
    ) in media_types:
        for entity_title, results in data[media_type].items():
            if len(results) <= 1:
                continue

            selected_match = choose_tmdb_match(
                entity_title,
                media_type,
                results,
                title_field,
                original_title_field,
                release_date_field,
            )
            if selected_match is None:
                continue

            data[media_type][entity_title] = [selected_match]
            selection_cache[media_type][entity_title] = selected_match["id"]
            write_json(selection_cache, cache_file_path)


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
        print(f"=== Pass {pass_counter}: Aggregating all show data ===")
        aggregate_show_data(shows, f"data/tvtime/{file}")
        write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
        pass_counter += 1

    print(f"=== Pass {pass_counter}: Aggregating all movie data ===")
    sort_episodes_asc(shows)
    aggregate_movie_data(movies, "data/tvtime/tracking-prod-records.csv")
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print(f"=== Pass {pass_counter}: Flatten dictionary into list ===")
    print("Flatten dictionary")
    aggregated = {
        # NOTE: The return type of values() is not a normal list and so not
        # serializable to JSON. We must convert it into a list first.
        "shows": list(aggregated["shows"].values()),
        "movies": list(aggregated["movies"].values()),
    }
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print(f"=== Pass {pass_counter}: Deduplicate episode list ===")
    dedupe_episode_list(aggregated["shows"])
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    # tmdb_data = fetch_tmdb_data(aggregated)
    tmdb_data = read_json("data/tvtime/tmdb_data.json")
    refetch_empty_tmdb_data(aggregated, tmdb_data)
    write_json(tmdb_data, "data/tvtime/tmdb_data.json")
    filter_tmdb_data(tmdb_data)

    if os.path.exists(path_from_project_root(TMDB_DETAILS_CACHE_PATH)):
        tmdb_details = read_json(TMDB_DETAILS_CACHE_PATH)
    else:
        tmdb_details = {"shows": {}, "movies": {}}

    print(f"=== Pass {pass_counter}: Fetch detail data")
    tmdb_details, fetch_failures = fetch_details(tmdb_data, tmdb_details)
    write_json(tmdb_details, TMDB_DETAILS_CACHE_PATH)

    if fetch_failures:
        for failure in fetch_failures:
            print(failure)
        raise RuntimeError(
            f"Failed to fetch {len(fetch_failures)} TMDB detail entries."
        )

    print(f"=== Pass {pass_counter}: Enrich data")
    enrich_data(aggregated, tmdb_data, tmdb_details)
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    write_json(aggregated, "data/tvtime/watch_data_final.json")


if __name__ == "__main__":
    main()
