"""Run the TV Time conversion pipeline."""

import os

from utils.path_utils import path_from_project_root

from .file_utils import write_json
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
    enrich_watch_data,
    fetch_details,
    filter_tmdb_search_data,
    read_tmdb_cache,
    search_tmdb_for_missing,
    validate_tmdb_details_cache,
    validate_tmdb_search_cache,
)
from .tv_data import (
    aggregate_movie_data,
    aggregate_show_data,
    deduplicate_show_episodes,
    sort_episodes_ascending,
)


def main() -> None:
    """Run the complete TV Time conversion and TMDB enrichment pipeline.

    The function reads the fixed CSV and cache paths under ``data/tvtime``,
    writes a snapshot after each major conversion stage, and regenerates
    ``watch_data_final.json`` as the stable path to the latest output. Raw TMDB
    search results are saved before candidate filtering, while detail fetching
    and enrichment use the filtered results.

    This command prints progress, can prompt for ambiguous TMDB matches, makes
    network requests when cache entries are missing, and requires
    ``TMDB_TOKEN`` for those requests. Unhandled file, cache-validation, and
    network errors stop the pipeline. Detail request failures are collected and
    then stop final enrichment, while titles left without a selected ID remain
    unresolved and continue through the pipeline with metadata defaults.
    """
    shows: ShowIndex = {}
    movies: MovieIndex = {}
    indexed_watch_data: IndexedWatchData = {"shows": shows, "movies": movies}
    show_csv_filenames = [
        "tracking-prod-records-v2.csv",
        "show_seen_episode_latest.csv",
        "followed_tv_show.csv",
        "seen_episode_latest.csv",
        "tracking-prod-records.csv",
        "user_tv_show_data.csv",
    ]
    snapshot_number = 1
    for show_csv_filename in show_csv_filenames:
        print("=== Aggregating all show data ===")
        aggregate_show_data(shows, f"data/tvtime/{show_csv_filename}")
        write_json(
            indexed_watch_data,
            f"data/tvtime/watch_data_{snapshot_number}.json",
        )
        snapshot_number += 1

    print("=== Sort episodes ===")
    sort_episodes_ascending(shows)
    write_json(
        indexed_watch_data,
        f"data/tvtime/watch_data_{snapshot_number}.json",
    )
    snapshot_number += 1

    print("=== Aggregating all movie data ===")
    aggregate_movie_data(movies, "data/tvtime/tracking-prod-records.csv")
    write_json(
        indexed_watch_data,
        f"data/tvtime/watch_data_{snapshot_number}.json",
    )
    snapshot_number += 1

    print("=== Flatten dictionary into list ===")
    aggregated_watch_data: AggregatedWatchData = {
        "shows": list(shows.values()),
        "movies": list(movies.values()),
    }
    write_json(
        aggregated_watch_data,
        f"data/tvtime/watch_data_{snapshot_number}.json",
    )
    snapshot_number += 1

    print("=== Deduplicate episode list ===")
    deduplicate_show_episodes(aggregated_watch_data["shows"])
    write_json(
        aggregated_watch_data,
        f"data/tvtime/watch_data_{snapshot_number}.json",
    )
    snapshot_number += 1

    print("=== Search TMDB ===")
    tmdb_search_data: TMDBSearchData
    if os.path.exists(path_from_project_root(TMDB_SEARCH_CACHE_PATH)):
        tmdb_search_data = validate_tmdb_search_cache(
            read_tmdb_cache(TMDB_SEARCH_CACHE_PATH), TMDB_SEARCH_CACHE_PATH
        )
    else:
        tmdb_search_data = {"shows": {}, "movies": {}}
    search_tmdb_for_missing(aggregated_watch_data, tmdb_search_data)
    write_json(tmdb_search_data, TMDB_SEARCH_CACHE_PATH)

    print("=== Filter TMDB search queries ===")
    filter_tmdb_search_data(tmdb_search_data)
    write_json(tmdb_search_data, TMDB_FILTERED_SEARCH_CACHE_PATH)

    print("=== Fetch detail data ===")
    tmdb_details: TMDBDetailsData
    if os.path.exists(path_from_project_root(TMDB_DETAILS_CACHE_PATH)):
        tmdb_details = validate_tmdb_details_cache(
            read_tmdb_cache(TMDB_DETAILS_CACHE_PATH), TMDB_DETAILS_CACHE_PATH
        )
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
    enrich_watch_data(aggregated_watch_data, tmdb_search_data, tmdb_details)
    write_json(
        aggregated_watch_data,
        f"data/tvtime/watch_data_{snapshot_number}.json",
    )
    write_json(aggregated_watch_data, "data/tvtime/watch_data_final.json")


if __name__ == "__main__":
    main()
