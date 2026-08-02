"""TMDB search, matching, caching, and metadata enrichment."""

import json
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
TMDB_SELECTION_CACHE_PATH = "data/tvtime/tmdb_selection_cache.json"
TMDB_REQUEST_TIMEOUT = 30
TMDB_REQUEST_INTERVAL = 1 / 3

SHOW_NON_LIST_FIELDS = (
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
MOVIE_NON_LIST_FIELDS = (
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


def read_tmdb_cache(cache_path: str) -> object:
    """Read a TMDB cache and add its path to file or JSON errors.

    Structure validation is handled separately because each cache type has a
    different schema.
    """
    try:
        return read_json(cache_path)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Could not read TMDB cache at {cache_path}: {error}"
        ) from error


def _require_tmdb_cache_sections(data: object, cache_path: str) -> dict[str, object]:
    """Return a cache object containing dictionary show and movie sections."""
    if not isinstance(data, dict):
        raise TypeError(f"Invalid TMDB cache at {cache_path}: expected a JSON object.")

    for media_type in ("shows", "movies"):
        if not isinstance(data.get(media_type), dict):
            raise TypeError(
                f"Invalid TMDB cache at {cache_path}: expected '{media_type}' "
                "to be a JSON object."
            )

    return cast(dict[str, object], data)


def validate_tmdb_search_cache(data: object, cache_path: str) -> TMDBSearchData:
    """Validate the container structure used by a TMDB search cache.

    Candidate entries are deliberately not validated here. Filtering handles
    malformed candidates separately so one bad result does not invalidate the
    entire cache.
    """
    cache = _require_tmdb_cache_sections(data, cache_path)
    for media_type in ("shows", "movies"):
        section = cast(dict[object, object], cache[media_type])
        for source_title, candidates in section.items():
            if not isinstance(source_title, str) or not isinstance(candidates, list):
                raise TypeError(
                    f"Invalid TMDB search cache at {cache_path}: expected every "
                    f"'{media_type}' entry to map a title to a candidate list."
                )

    return cast(TMDBSearchData, cache)


def validate_tmdb_selection_cache(data: object, cache_path: str) -> TMDBSelectionCache:
    """Validate title-to-integer-ID mappings in a manual-selection cache."""
    cache = _require_tmdb_cache_sections(data, cache_path)
    for media_type in ("shows", "movies"):
        section = cast(dict[object, object], cache[media_type])
        for source_title, tmdb_id in section.items():
            if not isinstance(source_title, str) or type(tmdb_id) is not int:
                raise TypeError(
                    f"Invalid TMDB selection cache at {cache_path}: expected every "
                    f"'{media_type}' entry to map a title to an integer TMDB ID."
                )

    return cast(TMDBSelectionCache, cache)


def validate_tmdb_details_cache(data: object, cache_path: str) -> TMDBDetailsData:
    """Validate ID-keyed show and movie detail mappings from a cache."""
    cache = _require_tmdb_cache_sections(data, cache_path)
    for media_type in ("shows", "movies"):
        section = cast(dict[object, object], cache[media_type])
        for cache_key, detail in section.items():
            if (
                not isinstance(cache_key, str)
                or not isinstance(detail, dict)
                or type(detail.get("id")) is not int
            ):
                raise TypeError(
                    f"Invalid TMDB details cache at {cache_path}: expected every "
                    f"'{media_type}' entry to use a string TMDB ID key matching "
                    "an integer detail ID."
                )
            if cache_key != str(detail["id"]):
                raise ValueError(
                    f"Invalid TMDB details cache at {cache_path}: key {cache_key!r} "
                    f"does not match detail ID {detail['id']!r}."
                )

    return cast(TMDBDetailsData, cache)


def parse_title_and_year(name: str) -> tuple[str, str | None]:
    """Return a title and its trailing ``(YYYY)`` year, if present."""
    match = re.fullmatch(r"(.+) \((\d{4})\)", name)
    if match:
        return match.group(1), match.group(2)
    return name, None


def search_tmdb(aggregated_watch_data: AggregatedWatchData) -> TMDBSearchData:
    """Return all TMDB search results for each show and movie."""
    print("Fetching search results")
    api_key = os.getenv("TMDB_TOKEN")
    if not api_key:
        raise RuntimeError("TMDB_TOKEN is required to fetch TMDB data.")
    headers = {"Authorization": f"Bearer {api_key}"}
    search_data: TMDBSearchData = {"shows": {}, "movies": {}}

    endpoints = {
        "shows": f"{TMDB_API_BASE_URL}/search/tv",
        "movies": f"{TMDB_API_BASE_URL}/search/movie",
    }

    for media_type, endpoint in endpoints.items():
        for media_record in aggregated_watch_data[media_type]:
            search_candidates: list[TMDBSearchCandidate] = []
            page = 1
            total_pages = 1
            search_title, _ = parse_title_and_year(media_record["name"])

            print(f"Fetching search results for {media_record['name']}")
            while page <= total_pages:
                print(f"Fetching page {page} of paginaged search results.")
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params={"query": search_title, "page": page},
                    timeout=TMDB_REQUEST_TIMEOUT,
                )
                time.sleep(TMDB_REQUEST_INTERVAL)
                response.raise_for_status()

                search_page = cast(TMDBSearchPage, response.json())
                search_candidates.extend(search_page["results"])
                total_pages = search_page["total_pages"]
                page += 1

            search_data[media_type][media_record["name"]] = search_candidates

    return search_data


def get_single_candidate_id(candidates: object) -> int | None:
    """Return the ID from a single-result list if its type is exactly ``int``."""
    if not isinstance(candidates, list) or len(candidates) != 1:
        return None

    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return None

    tmdb_id = candidate.get("id")
    return tmdb_id if type(tmdb_id) is int else None


def is_valid_tmdb_detail(detail: object, tmdb_id: int) -> bool:
    """Return whether ``detail`` is a dictionary with the expected TMDB ID."""
    return (
        isinstance(detail, dict)
        and type(detail.get("id")) is int
        and detail.get("id") == tmdb_id
    )


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
    candidate: Mapping[str, object], date_field: str, expected_year: str | None
) -> bool:
    candidate_date = candidate.get(date_field)
    return bool(
        expected_year
        and isinstance(candidate_date, str)
        and candidate_date.startswith(expected_year)
    )


def fetch_tmdb_alternative_titles(media_type: str, tmdb_id: int) -> list[str]:
    """Fetch alternative titles for one candidate, returning title strings."""
    api_key = os.getenv("TMDB_TOKEN")
    if not api_key:
        return []

    tmdb_media_type = "tv" if media_type == "shows" else "movie"
    response = requests.get(
        f"{TMDB_API_BASE_URL}/{tmdb_media_type}/{tmdb_id}/alternative_titles",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TMDB_REQUEST_TIMEOUT,
    )
    try:
        response.raise_for_status()
        alternative_title_data = response.json()
    finally:
        time.sleep(TMDB_REQUEST_INTERVAL)

    if not isinstance(alternative_title_data, dict):
        raise TypeError("TMDB alternative-title response is not an object.")
    title_entries = alternative_title_data.get(
        "results" if media_type == "shows" else "titles", []
    )
    if not isinstance(title_entries, list):
        return []
    return [
        title_entry["title"]
        for title_entry in title_entries
        if isinstance(title_entry, dict) and isinstance(title_entry.get("title"), str)
    ]


def fetch_details(
    tmdb_search_data: TMDBSearchData, details: TMDBDetailsData
) -> tuple[TMDBDetailsData, list[str]]:
    """Return TMDB details and errors for entries with one selected result."""
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
        for source_title, search_candidates in tmdb_search_data[media_type].items():
            progress += 1
            progress_prefix = (
                f"[{progress}/{total_entries}] {media_type[:-1].title()}: "
            )
            tmdb_id = get_single_candidate_id(search_candidates)
            if tmdb_id is None:
                print(f"{progress_prefix}{source_title} (no selected ID)")
                unresolved_count += 1
                continue

            detail_cache = details[media_type]
            cache_key = str(tmdb_id)
            if is_valid_tmdb_detail(detail_cache.get(cache_key), tmdb_id):
                print(f"{progress_prefix}{source_title} (cached)")
                cached_count += 1
                continue

            request_key = (media_type, tmdb_id)
            if request_key in attempted_ids:
                print(f"{progress_prefix}{source_title} (previous request failed)")
                continue
            attempted_ids.add(request_key)

            if headers is None:
                print(f"{progress_prefix}{source_title} (failed)")
                failures.append(
                    f"Cannot fetch {media_type[:-1]} {source_title} ({tmdb_id}): "
                    "TMDB_TOKEN is not set."
                )
                continue

            print(f"{progress_prefix}{source_title} (fetching)")
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
                    f"Could not fetch {media_type[:-1]} {source_title} ({tmdb_id}): "
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


def add_missing_metadata_defaults(
    record: dict[str, JSONValue],
    non_list_fields: tuple[str, ...],
    list_fields: tuple[str, ...],
) -> None:
    """Set missing non-list fields to ``None`` and list fields to empty lists."""
    for field in non_list_fields:
        record.setdefault(field, None)
    for field in list_fields:
        record.setdefault(field, [])


def enrich_watch_data(
    aggregated_watch_data: AggregatedWatchData,
    tmdb_search_data: TMDBSearchData,
    tmdb_details: TMDBDetailsData,
) -> None:
    """Copy allowed TMDB detail fields into ``aggregated_watch_data`` in place."""
    media_type_configs = (
        ("shows", SHOW_NON_LIST_FIELDS, SHOW_LIST_FIELDS),
        ("movies", MOVIE_NON_LIST_FIELDS, MOVIE_LIST_FIELDS),
    )

    for media_type, non_list_fields, list_fields in media_type_configs:
        for watch_record in aggregated_watch_data[media_type]:
            source_title = watch_record["name"]
            add_missing_metadata_defaults(
                cast(dict[str, JSONValue], watch_record),
                non_list_fields,
                list_fields,
            )

            if media_type == "shows":
                show_record = cast(ShowWatchData, watch_record)
                for episode in show_record["episodes_watched"]:
                    add_missing_metadata_defaults(
                        cast(dict[str, JSONValue], episode), EPISODE_METADATA_FIELDS, ()
                    )

            tmdb_id = get_single_candidate_id(
                tmdb_search_data[media_type].get(source_title)
            )
            if tmdb_id is None:
                continue

            if media_type == "shows":
                detail = tmdb_details.get("shows", {}).get(str(tmdb_id))
            else:
                detail = tmdb_details.get("movies", {}).get(str(tmdb_id))
            if not is_valid_tmdb_detail(detail, tmdb_id):
                raise RuntimeError(
                    f"Missing cached TMDB detail for {media_type[:-1]} "
                    f"{source_title} ({tmdb_id})."
                )

            detail_data = cast(Mapping[str, object], detail)
            for field in (*non_list_fields, *list_fields):
                if field in detail_data:
                    cast(dict[str, JSONValue], watch_record)[field] = cast(
                        JSONValue, detail_data[field]
                    )

            if media_type == "shows":
                canonical_name = detail_data.get("name")
                if isinstance(canonical_name, str) and canonical_name.strip():
                    cast(ShowWatchData, watch_record)["name"] = canonical_name
            else:
                canonical_title = detail_data.get("title")
                if isinstance(canonical_title, str) and canonical_title.strip():
                    cast(MovieWatchData, watch_record)["name"] = canonical_title
                    cast(MovieWatchData, watch_record)["title"] = canonical_title


def search_tmdb_for_missing(
    aggregated_watch_data: AggregatedWatchData, tmdb_search_data: TMDBSearchData
) -> None:
    """Search for watch records with absent or empty cached results."""
    media_needing_search: AggregatedWatchData = {"shows": [], "movies": []}

    for media_type in ("shows", "movies"):
        cached_results = tmdb_search_data.setdefault(media_type, {})

        for media_record in aggregated_watch_data[media_type]:
            # If it exists and is non-empty
            if cached_results.get(media_record["name"]):
                continue
            if media_type == "shows":
                media_needing_search["shows"].append(
                    cast(ShowWatchData, media_record)
                )
            else:
                media_needing_search["movies"].append(
                    cast(MovieWatchData, media_record)
                )

    if not media_needing_search["shows"] and not media_needing_search["movies"]:
        return

    search_results = search_tmdb(media_needing_search)
    for media_type in ("shows", "movies"):
        tmdb_search_data[media_type].update(search_results[media_type])


def filter_tmdb_candidates(
    candidates: list[object],
    source_title: str,
    title_field: str,
    original_title_field: str,
    date_field: str,
    cached_tmdb_id: int | None,
    alternative_titles: dict[int, list[str]] | None = None,
) -> tuple[list[TMDBSearchCandidate], str]:
    """Filter candidates and return the evidence used for the selection."""
    valid_candidates = [
        cast(TMDBSearchCandidate, candidate)
        for candidate in candidates
        if isinstance(candidate, dict)
    ]
    lookup_title, lookup_year = parse_title_and_year(source_title)
    cached_match = next(
        (candidate for candidate in valid_candidates if candidate.get("id") == cached_tmdb_id),
        None,
    )
    direct_title_matches = [
        candidate
        for candidate in valid_candidates
        if tmdb_title_matches(
            candidate, lookup_title, title_field, original_title_field
        )
    ]
    title_matches = direct_title_matches

    if not title_matches and alternative_titles is not None:
        normalized_lookup_title = normalize_tmdb_title(lookup_title)
        title_matches = [
            candidate
            for candidate in valid_candidates
            if _has_alternative_title(
                candidate, normalized_lookup_title, alternative_titles
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
            cached_match, date_field, lookup_year
        )
        if cached_title_matches and cached_year_matches:
            return [cached_match], "cached manual selection"

        review_candidates = title_matches or [cached_match]
        return review_candidates, "cached selection conflicts with title or year"

    if not title_matches:
        return valid_candidates, match_type

    if lookup_year:
        year_matches = [
            candidate
            for candidate in title_matches
            if tmdb_date_matches(candidate, date_field, lookup_year)
        ]
        if len(year_matches) == 1:
            return year_matches, f"{match_type} and year"
        return year_matches or title_matches, f"{match_type} has no unique year match"

    if len(title_matches) == 1:
        return title_matches, match_type
    return title_matches, f"{match_type} is ambiguous"


def choose_tmdb_match(
    source_title: str,
    media_type: str,
    candidates: list[TMDBSearchCandidate],
    title_field: str,
    original_title_field: str,
    date_field: str,
    reason: str,
) -> TMDBSearchCandidate | None:
    """Return the TMDB candidate selected through standard input, or ``None``."""
    print(f"\n\n\nReview {media_type[:-1]} match for {source_title}:")
    print(f"Reason: {reason}")
    for index, candidate in enumerate(candidates, start=1):
        candidate_date = candidate.get(date_field)
        tmdb_id = candidate.get("id")
        print(f"{index}.")
        print("-----")
        print(
            f"{candidate.get(title_field) or '<Unknown>'} | "
            f"{candidate.get(original_title_field) or '<Unknown>'} | "
            f"{candidate_date or '<Unknown>'} | "
            f"{tmdb_id if tmdb_id is not None else '<Unknown>'}"
        )
        print(f"Description: {candidate.get('overview') or '<Unknown>'}")
        print("-----")

    while True:
        choice = input(
            "Choose a match by number, or type s/skip to leave unresolved: "
        ).strip()
        if choice.lower() in ("s", "skip"):
            return None
        if choice.isdigit():
            choice_number = int(choice)
            if 1 <= choice_number <= len(candidates):
                return candidates[choice_number - 1]
        print(f"Enter a number from 1 to {len(candidates)}.")


def _has_alternative_title(
    candidate: TMDBSearchCandidate,
    normalized_lookup_title: str,
    alternative_titles: dict[int, list[str]],
) -> bool:
    candidate_id = candidate.get("id")
    if type(candidate_id) is not int:
        return False
    return any(
        normalize_tmdb_title(title) == normalized_lookup_title
        for title in alternative_titles.get(candidate_id, [])
    )


def filter_tmdb_search_data(tmdb_search_data: TMDBSearchData) -> None:
    """Reduce candidate lists in place and persist manual selection IDs.

    The caller owns persistence of the filtered search data. This function
    writes only the separate manual-selection cache when a choice is made.
    """
    if os.path.exists(path_from_project_root(TMDB_SELECTION_CACHE_PATH)):
        selection_cache = validate_tmdb_selection_cache(
            read_tmdb_cache(TMDB_SELECTION_CACHE_PATH), TMDB_SELECTION_CACHE_PATH
        )
    else:
        selection_cache: TMDBSelectionCache = {"shows": {}, "movies": {}}

    media_type_configs = (
        ("shows", "name", "original_name", "first_air_date"),
        ("movies", "title", "original_title", "release_date"),
    )
    review_entries: dict[
        tuple[str, str],
        tuple[list[TMDBSearchCandidate], str, tuple[str, str, str]],
    ] = {}
    alternative_titles_cache: dict[tuple[str, int], list[str]] = {}

    for (
        media_type,
        title_field,
        original_title_field,
        date_field,
    ) in media_type_configs:
        for source_title, search_candidates in tmdb_search_data[media_type].items():
            valid_search_candidates = [
                cast(TMDBSearchCandidate, candidate)
                for candidate in search_candidates
                if isinstance(candidate, dict)
            ]
            malformed_count = len(search_candidates) - len(valid_search_candidates)
            if malformed_count:
                candidate_label = "candidate" if malformed_count == 1 else "candidates"
                print(
                    f"Skipping {malformed_count} malformed TMDB {candidate_label} "
                    f"for {media_type[:-1]} {source_title}."
                )

            filtered_results, reason = filter_tmdb_candidates(
                cast(list[object], valid_search_candidates),
                source_title,
                title_field,
                original_title_field,
                date_field,
                selection_cache[media_type].get(source_title),
            )
            if reason == "no exact title match" and valid_search_candidates:
                alternative_titles: dict[int, list[str]] = {}
                for candidate in valid_search_candidates:
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
                                f"{media_type[:-1]} {source_title} ({tmdb_id}): {error}"
                            )
                            alternative_titles_cache[cache_key] = []
                    alternative_titles[tmdb_id] = alternative_titles_cache[cache_key]

                filtered_results, reason = filter_tmdb_candidates(
                    cast(list[object], valid_search_candidates),
                    source_title,
                    title_field,
                    original_title_field,
                    date_field,
                    selection_cache[media_type].get(source_title),
                    alternative_titles,
                )

            tmdb_search_data[media_type][source_title] = filtered_results
            if reason not in {
                "cached manual selection",
                "exact title",
                "exact title and year",
                "alternative title",
                "alternative title and year",
            }:
                review_entries[(media_type, source_title)] = (
                    filtered_results,
                    reason,
                    (title_field, original_title_field, date_field),
                )

    print(f"Entries requiring review: {len(review_entries)}")

    for (media_type, source_title), (
        search_candidates,
        reason,
        review_fields,
    ) in review_entries.items():
        if not search_candidates:
            print(f"No TMDB candidates for {media_type[:-1]} {source_title}.")
            continue

        title_field, original_title_field, date_field = review_fields
        selected_match = choose_tmdb_match(
            source_title,
            media_type,
            search_candidates,
            title_field,
            original_title_field,
            date_field,
            reason,
        )
        if selected_match is None:
            continue

        tmdb_search_data[media_type][source_title] = [selected_match]
        selected_tmdb_id = selected_match.get("id")
        if type(selected_tmdb_id) is int:
            selection_cache[media_type][source_title] = selected_tmdb_id
        write_json(selection_cache, TMDB_SELECTION_CACHE_PATH)
