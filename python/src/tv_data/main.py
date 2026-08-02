"""Run the TV Time conversion pipeline."""

import os
from typing import cast

from utils.path_utils import path_from_project_root

from .file_utils import read_json, write_json
from .models import (
    AggregatedWatchData,
    IndexedWatchData,
    MovieIndex,
    ShowIndex,
    TMDBDetailsData,
    TMDBSearchData,
)
from .tmdb import (
    TMDB_DETAILS_CACHE_PATH,
    TMDB_FILTERED_SEARCH_CACHE_PATH,
    TMDB_SEARCH_CACHE_PATH,
    enrich_data,
    fetch_details,
    filter_tmdb_data,
    search_tmdb_for_missing,
)
from .tv_data import (
    aggregate_movie_data,
    aggregate_show_data,
    dedupe_episode_list,
    sort_episodes_asc,
)


def main() -> None:
    """Convert TV Time CSV exports into JSON with TMDB metadata."""
    shows: ShowIndex = {}
    movies: MovieIndex = {}
    indexed_data: IndexedWatchData = {"shows": shows, "movies": movies}
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
        print("=== Aggregating all show data ===")
        aggregate_show_data(shows, f"data/tvtime/{file}")
        write_json(indexed_data, f"data/tvtime/watch_data_{pass_counter}.json")
        pass_counter += 1

    print("=== Sort episodes ===")
    sort_episodes_asc(shows)
    write_json(indexed_data, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print("=== Aggregating all movie data ===")
    aggregate_movie_data(movies, "data/tvtime/tracking-prod-records.csv")
    write_json(indexed_data, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print("=== Flatten dictionary into list ===")
    aggregated: AggregatedWatchData = {
        "shows": list(shows.values()),
        "movies": list(movies.values()),
    }
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print("=== Deduplicate episode list ===")
    dedupe_episode_list(aggregated["shows"])
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    pass_counter += 1

    print("=== Search TMDB ===")
    tmdb_search_data: TMDBSearchData
    if os.path.exists(path_from_project_root(TMDB_SEARCH_CACHE_PATH)):
        tmdb_search_data = cast(TMDBSearchData, read_json(TMDB_SEARCH_CACHE_PATH))
    else:
        tmdb_search_data = {"shows": {}, "movies": {}}
    search_tmdb_for_missing(aggregated, tmdb_search_data)
    write_json(tmdb_search_data, TMDB_SEARCH_CACHE_PATH)

    print("=== Filter TMDB search queries ===")
    filter_tmdb_data(tmdb_search_data)
    write_json(tmdb_search_data, TMDB_FILTERED_SEARCH_CACHE_PATH)

    print("=== Fetch detail data ===")
    tmdb_details: TMDBDetailsData
    if os.path.exists(path_from_project_root(TMDB_DETAILS_CACHE_PATH)):
        tmdb_details = cast(TMDBDetailsData, read_json(TMDB_DETAILS_CACHE_PATH))
    else:
        tmdb_details = {"shows": {}, "movies": {}}
    tmdb_details, fetch_failures = fetch_details(tmdb_search_data, tmdb_details)
    write_json(tmdb_details, TMDB_DETAILS_CACHE_PATH)

    if fetch_failures:
        for failure in fetch_failures:
            print(failure)
        raise RuntimeError(
            f"Failed to fetch {len(fetch_failures)} TMDB detail entries."
        )

    print("=== Enrich data ===")
    enrich_data(aggregated, tmdb_search_data, tmdb_details)
    write_json(aggregated, f"data/tvtime/watch_data_{pass_counter}.json")
    write_json(aggregated, "data/tvtime/watch_data_final.json")


if __name__ == "__main__":
    main()
