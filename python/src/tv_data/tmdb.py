"""TMDB search, matching, caching, and metadata enrichment."""

import os
import re
import time
import unicodedata
from collections.abc import Mapping
from typing import cast

import requests

from utils.path_utils import path_from_project_root

from .file_utils import read_json, write_json
from .models import (
    AggregatedWatchData,
    JSONValue,
    MovieWatchData,
    ShowWatchData,
    TMDBDetailsData,
    TMDBMovieDetail,
    TMDBSearchCandidate,
    TMDBSearchData,
    TMDBSearchPage,
    TMDBSelectionCache,
    TMDBShowDetail,
)

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_SEARCH_CACHE_PATH = "data/tvtime/tmdb_search_data.json"
TMDB_FILTERED_SEARCH_CACHE_PATH = "data/tvtime/tmdb_search_data_filtered.json"
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


def tmdb_lookup_title_and_year(name: str) -> tuple[str, str | None]:
    """Return a title and its trailing ``(YYYY)`` year, if present."""
    match = re.fullmatch(r"(.+) \((\d{4})\)", name)
    if match:
        return match.group(1), match.group(2)
    return name, None


def _search_page(payload: object) -> TMDBSearchPage:
    """Treat a decoded TMDB search response as a search page."""
    return cast(TMDBSearchPage, payload)


def search_tmdb(aggregated: AggregatedWatchData) -> TMDBSearchData:
    """Return all TMDB search results for each show and movie."""
    print("Fetching search results")
    api_key = os.getenv("TMDB_TOKEN")
    if not api_key:
        raise RuntimeError("TMDB_TOKEN is required to fetch TMDB data.")
    headers = {"Authorization": f"Bearer {api_key}"}
    data: TMDBSearchData = {"shows": {}, "movies": {}}

    endpoints = {
        "shows": f"{TMDB_API_BASE_URL}/search/tv",
        "movies": f"{TMDB_API_BASE_URL}/search/movie",
    }

    for media_type, endpoint in endpoints.items():
        for media in aggregated[media_type]:
            results: list[TMDBSearchCandidate] = []
            page = 1
            total_pages = 1
            query_name, _ = tmdb_lookup_title_and_year(media["name"])

            print(f"Fetching search results for {media['name']}")
            while page <= total_pages:
                print(f"Fetching page {page} of paginaged search results.")
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params={"query": query_name, "page": page},
                    timeout=TMDB_REQUEST_TIMEOUT,
                )
                time.sleep(TMDB_REQUEST_INTERVAL)
                response.raise_for_status()

                result = _search_page(response.json())
                results.extend(result["results"])
                total_pages = result["total_pages"]
                page += 1

            data[media_type][media["name"]] = results

    return data


def selected_tmdb_id(results: object) -> int | None:
    """Return the ID from a single-result list if its type is exactly ``int``."""
    if not isinstance(results, list) or len(results) != 1:
        return None

    candidate = results[0]
    if not isinstance(candidate, dict):
        return None

    tmdb_id = candidate.get("id")
    return tmdb_id if type(tmdb_id) is int else None


def is_valid_tmdb_detail(detail: object, tmdb_id: int) -> bool:
    """Return whether ``detail`` is a dictionary with the expected TMDB ID."""
    return isinstance(detail, dict) and detail.get("id") == tmdb_id


def normalize_tmdb_title(title: str) -> str:
    """Normalize only Unicode canonical equivalents for title comparison."""
    return unicodedata.normalize("NFC", title)


def tmdb_title_matches(
    candidate: Mapping[str, object],
    lookup_title: str,
    title_field: str,
    original_title_field: str,
) -> bool:
    candidate_titles = (
        candidate.get(title_field),
        candidate.get(original_title_field),
    )
    normalized_lookup_title = normalize_tmdb_title(lookup_title)
    return any(
        isinstance(title, str)
        and normalize_tmdb_title(title) == normalized_lookup_title
        for title in candidate_titles
    )


def tmdb_date_matches(
    candidate: Mapping[str, object], release_date_field: str, year: str | None
) -> bool:
    release_date = candidate.get(release_date_field)
    return bool(
        year and isinstance(release_date, str) and release_date.startswith(year)
    )


def fetch_tmdb_alternative_titles(media_type: str, tmdb_id: int) -> list[str]:
    """Fetch alternative titles for one candidate, returning title strings."""
    api_key = os.getenv("TMDB_TOKEN")
    if not api_key:
        return []

    endpoint_type = "tv" if media_type == "shows" else "movie"
    response = requests.get(
        f"{TMDB_API_BASE_URL}/{endpoint_type}/{tmdb_id}/alternative_titles",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TMDB_REQUEST_TIMEOUT,
    )
    try:
        response.raise_for_status()
        result = response.json()
    finally:
        time.sleep(TMDB_REQUEST_INTERVAL)

    if not isinstance(result, dict):
        raise TypeError("TMDB alternative-title response is not an object.")
    title_entries = result.get("results" if media_type == "shows" else "titles", [])
    if not isinstance(title_entries, list):
        return []
    return [
        title_entry["title"]
        for title_entry in title_entries
        if isinstance(title_entry, dict) and isinstance(title_entry.get("title"), str)
    ]


def fetch_details(
    tmdb_search_data: TMDBSearchData, cached_details: object
) -> tuple[TMDBDetailsData, list[str]]:
    """Return TMDB details and errors for entries with one selected result."""
    raw_details = (
        cast(dict[str, object], cached_details)
        if isinstance(cached_details, dict)
        else {}
    )
    raw_shows = raw_details.get("shows")
    raw_movies = raw_details.get("movies")
    details: TMDBDetailsData = {
        "shows": (
            cast(dict[str, TMDBShowDetail], raw_shows)
            if isinstance(raw_shows, dict)
            else {}
        ),
        "movies": (
            cast(dict[str, TMDBMovieDetail], raw_movies)
            if isinstance(raw_movies, dict)
            else {}
        ),
    }

    endpoints = {
        "shows": f"{TMDB_API_BASE_URL}/tv",
        "movies": f"{TMDB_API_BASE_URL}/movie",
    }
    api_key = os.getenv("TMDB_TOKEN")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    failures: list[str] = []
    attempted_ids: set[tuple[str, int]] = set()
    total_entries = sum(len(tmdb_search_data[media_type]) for media_type in endpoints)
    cached_count = 0
    fetched_count = 0
    unresolved_count = 0
    progress = 0
    request_count = 0

    for media_type in ("shows", "movies"):
        for migration_name, results in tmdb_search_data[media_type].items():
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
                if media_type == "shows":
                    details["shows"][cache_key] = cast(TMDBShowDetail, detail)
                else:
                    details["movies"][cache_key] = cast(TMDBMovieDetail, detail)
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
    entry: dict[str, JSONValue],
    scalar_fields: tuple[str, ...],
    list_fields: tuple[str, ...],
) -> None:
    """Set missing scalar fields to ``None`` and list fields to empty lists."""
    for field in scalar_fields:
        entry.setdefault(field, None)
    for field in list_fields:
        entry.setdefault(field, [])


def enrich_data(
    aggregated: AggregatedWatchData,
    tmdb_data: TMDBSearchData,
    tmdb_details: TMDBDetailsData,
) -> None:
    """Copy allowed TMDB detail fields into ``aggregated`` in place."""
    media_types = (
        ("shows", SHOW_SCALAR_FIELDS, SHOW_LIST_FIELDS),
        ("movies", MOVIE_SCALAR_FIELDS, MOVIE_LIST_FIELDS),
    )

    for media_type, scalar_fields, list_fields in media_types:
        for entry in aggregated[media_type]:
            migration_name = entry["name"]
            add_metadata_defaults(
                cast(dict[str, JSONValue], entry), scalar_fields, list_fields
            )

            if media_type == "shows":
                show_entry = cast(ShowWatchData, entry)
                for episode in show_entry["episodes_watched"]:
                    add_metadata_defaults(
                        cast(dict[str, JSONValue], episode), EPISODE_METADATA_FIELDS, ()
                    )

            tmdb_id = selected_tmdb_id(tmdb_data[media_type].get(migration_name))
            if tmdb_id is None:
                continue

            if media_type == "shows":
                detail = tmdb_details.get("shows", {}).get(str(tmdb_id))
            else:
                detail = tmdb_details.get("movies", {}).get(str(tmdb_id))
            if not is_valid_tmdb_detail(detail, tmdb_id):
                raise RuntimeError(
                    f"Missing cached TMDB detail for {media_type[:-1]} "
                    f"{migration_name} ({tmdb_id})."
                )

            detail_data = cast(Mapping[str, object], detail)
            for field in (*scalar_fields, *list_fields):
                if field in detail_data:
                    cast(dict[str, JSONValue], entry)[field] = cast(
                        JSONValue, detail_data[field]
                    )

            if media_type == "shows":
                canonical_name = detail_data.get("name")
                if isinstance(canonical_name, str) and canonical_name.strip():
                    cast(ShowWatchData, entry)["name"] = canonical_name
            else:
                canonical_title = detail_data.get("title")
                if isinstance(canonical_title, str) and canonical_title.strip():
                    cast(MovieWatchData, entry)["name"] = canonical_title
                    cast(MovieWatchData, entry)["title"] = canonical_title


def search_tmdb_for_missing(
    aggregated: AggregatedWatchData, tmdb_search_data: TMDBSearchData
) -> None:
    """Search for aggregated media with absent or empty cached results."""
    missing_media: AggregatedWatchData = {"shows": [], "movies": []}

    for media_type in ("shows", "movies"):
        cached_results = tmdb_search_data.setdefault(media_type, {})

        for media in aggregated[media_type]:
            # If it exists and is non-empty
            if cached_results.get(media["name"]):
                continue
            if media_type == "shows":
                missing_media["shows"].append(cast(ShowWatchData, media))
            else:
                missing_media["movies"].append(cast(MovieWatchData, media))

    if not missing_media["shows"] and not missing_media["movies"]:
        return

    search_results = search_tmdb(missing_media)
    for media_type in ("shows", "movies"):
        tmdb_search_data[media_type].update(search_results[media_type])


def filter_tmdb_candidates(
    results: list[object],
    entity_title: str,
    title_field: str,
    original_title_field: str,
    release_date_field: str,
    cached_id: int | None,
    alternative_titles: dict[int, list[str]] | None = None,
) -> tuple[list[TMDBSearchCandidate], str]:
    """Filter candidates and return the evidence used for the result."""
    valid_results = [
        cast(TMDBSearchCandidate, match) for match in results if isinstance(match, dict)
    ]
    lookup_title, lookup_year = tmdb_lookup_title_and_year(entity_title)
    cached_match = next(
        (match for match in valid_results if match.get("id") == cached_id), None
    )
    direct_title_matches = [
        match
        for match in valid_results
        if tmdb_title_matches(match, lookup_title, title_field, original_title_field)
    ]
    title_matches = direct_title_matches

    if not title_matches and alternative_titles is not None:
        normalized_lookup_title = normalize_tmdb_title(lookup_title)
        title_matches = [
            match
            for match in valid_results
            if _has_alternative_title(
                match, normalized_lookup_title, alternative_titles
            )
        ]
        match_type = "alternative title" if title_matches else "no exact title match"
    elif title_matches:
        match_type = "exact title"
    else:
        match_type = "no exact title match"

    if cached_match is not None:
        cached_title_matches = cached_match in direct_title_matches
        cached_year_matches = not lookup_year or tmdb_date_matches(
            cached_match, release_date_field, lookup_year
        )
        if cached_title_matches and cached_year_matches:
            return [cached_match], "cached manual selection"

        review_candidates = title_matches or [cached_match]
        return review_candidates, "cached selection conflicts with title or year"

    if not title_matches:
        return valid_results, match_type

    if lookup_year:
        year_matches = [
            match
            for match in title_matches
            if tmdb_date_matches(match, release_date_field, lookup_year)
        ]
        if len(year_matches) == 1:
            return year_matches, f"{match_type} and year"
        return year_matches or title_matches, f"{match_type} has no unique year match"

    if len(title_matches) == 1:
        return title_matches, match_type
    return title_matches, f"{match_type} is ambiguous"


def choose_tmdb_match(
    entity_title: str,
    media_type: str,
    results: list[TMDBSearchCandidate],
    title_field: str,
    original_title_field: str,
    release_date_field: str,
    reason: str,
) -> TMDBSearchCandidate | None:
    """Return the TMDB candidate selected through standard input, or ``None``."""
    print(f"\n\n\nReview {media_type[:-1]} match for {entity_title}:")
    print(f"Reason: {reason}")
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


def _has_alternative_title(
    candidate: TMDBSearchCandidate,
    lookup_title: str,
    alternative_titles: dict[int, list[str]],
) -> bool:
    candidate_id = candidate.get("id")
    if type(candidate_id) is not int:
        return False
    return any(
        normalize_tmdb_title(title) == lookup_title
        for title in alternative_titles.get(candidate_id, [])
    )


def filter_tmdb_data(tmdb_search_data: TMDBSearchData) -> None:
    """Reduce TMDB candidate lists in place and save manual selections."""
    cache_file_path = "data/tvtime/tmdb_selection_cache.json"
    if os.path.exists(path_from_project_root(cache_file_path)):
        selection_cache = cast(TMDBSelectionCache, read_json(cache_file_path))
    else:
        selection_cache: TMDBSelectionCache = {"shows": {}, "movies": {}}
    selection_cache.setdefault("shows", {})
    selection_cache.setdefault("movies", {})

    media_types = (
        ("shows", "name", "original_name", "first_air_date"),
        ("movies", "title", "original_title", "release_date"),
    )
    review_entries: dict[tuple[str, str], tuple[list[TMDBSearchCandidate], str]] = {}
    alternative_titles_cache: dict[tuple[str, int], list[str]] = {}

    for media_type, title_field, _, release_date_field in media_types:
        for entity_title, results in tmdb_search_data[media_type].items():
            original_title_field = (
                "original_name" if media_type == "shows" else "original_title"
            )
            filtered_results, reason = filter_tmdb_candidates(
                cast(list[object], results),
                entity_title,
                title_field,
                original_title_field,
                release_date_field,
                selection_cache[media_type].get(entity_title),
            )
            if reason == "no exact title match" and results:
                alternative_titles: dict[int, list[str]] = {}
                for candidate in results:
                    tmdb_id = candidate.get("id")
                    if type(tmdb_id) is not int:
                        continue
                    cache_key = (media_type, tmdb_id)
                    if cache_key not in alternative_titles_cache:
                        try:
                            alternative_titles_cache[cache_key] = (
                                fetch_tmdb_alternative_titles(media_type, tmdb_id)
                            )
                        except (
                            requests.RequestException,
                            TypeError,
                            ValueError,
                        ) as error:
                            print(
                                f"Could not fetch alternative titles for "
                                f"{media_type[:-1]} {entity_title} ({tmdb_id}): {error}"
                            )
                            alternative_titles_cache[cache_key] = []
                    alternative_titles[tmdb_id] = alternative_titles_cache[cache_key]

                filtered_results, reason = filter_tmdb_candidates(
                    cast(list[object], results),
                    entity_title,
                    title_field,
                    original_title_field,
                    release_date_field,
                    selection_cache[media_type].get(entity_title),
                    alternative_titles,
                )

            tmdb_search_data[media_type][entity_title] = filtered_results
            if reason not in {
                "cached manual selection",
                "exact title",
                "exact title and year",
                "alternative title",
                "alternative title and year",
            }:
                review_entries[(media_type, entity_title)] = (filtered_results, reason)

    print(f"Entries requiring review: {len(review_entries)}")

    for (media_type, entity_title), (results, reason) in review_entries.items():
        if not results:
            print(f"No TMDB candidates for {media_type[:-1]} {entity_title}.")
            continue

        title_field = "name" if media_type == "shows" else "title"
        original_title_field = (
            "original_name" if media_type == "shows" else "original_title"
        )
        release_date_field = (
            "first_air_date" if media_type == "shows" else "release_date"
        )
        selected_match = choose_tmdb_match(
            entity_title,
            media_type,
            results,
            title_field,
            original_title_field,
            release_date_field,
            reason,
        )
        if selected_match is None:
            continue

        tmdb_search_data[media_type][entity_title] = [selected_match]
        selected_id = selected_match.get("id")
        if type(selected_id) is int:
            selection_cache[media_type][entity_title] = selected_id
        write_json(selection_cache, cache_file_path)

    write_json(tmdb_search_data, TMDB_SEARCH_CACHE_PATH)
