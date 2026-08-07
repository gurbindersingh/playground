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
_AUTOMATIC_MATCH_REASONS = frozenset(
    {
        "exact title",
        "exact title and year",
    }
)
type TMDBReviewEntry = tuple[list[TMDBSearchCandidate], str, tuple[str, str, str]]
type TMDBReviewEntries = dict[tuple[str, str], TMDBReviewEntry]


def read_tmdb_cache(cache_path: str) -> object:
    """Decode a project-relative TMDB cache without assuming its schema.

    The decoded JSON value is returned as ``object`` because search, selection,
    and detail caches have different structures. File and JSON decoding errors
    are converted to ``ValueError`` with ``cache_path`` in the message; callers
    must then pass the value to the validator for that cache type.
    """
    try:
        return read_json(cache_path)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Could not read TMDB cache at {cache_path}: {error}"
        ) from error


def _require_tmdb_cache_sections(data: object, cache_path: str) -> dict[str, object]:
    """Verify the common top-level shape shared by every TMDB cache.

    A valid cache is a dictionary containing dictionary-valued ``shows`` and
    ``movies`` sections. The original dictionary is returned for further
    cache-specific validation. ``TypeError`` identifies the cache path and the
    missing or malformed section.
    """
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
    """Validate and return data read from a TMDB search cache.

    Each show or movie title must map to a list of candidates. Individual list
    entries are deliberately not validated here because filtering skips and
    reports malformed candidates instead of invalidating the complete cache.
    The input dictionary is returned unchanged or ``TypeError`` names the
    invalid cache structure.
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
    """Validate and return a cache of selected or unresolved TMDB IDs.

    Every show and movie title must map to a positive exact integer ID or
    ``None`` for a known unresolved title. Booleans, zero, and negative IDs are
    rejected. The original dictionary is returned or ``TypeError`` identifies
    the cache path and expected mapping.
    """
    cache = _require_tmdb_cache_sections(data, cache_path)
    for media_type in ("shows", "movies"):
        section = cast(dict[object, object], cache[media_type])
        for source_title, tmdb_id in section.items():
            if not isinstance(source_title, str) or (
                tmdb_id is not None and (type(tmdb_id) is not int or tmdb_id <= 0)
            ):
                raise TypeError(
                    f"Invalid TMDB selection cache at {cache_path}: expected every "
                    f"'{media_type}' entry to map a title to a positive integer "
                    "TMDB ID or null."
                )

    return cast(TMDBSelectionCache, cache)


def validate_tmdb_details_cache(data: object, cache_path: str) -> TMDBDetailsData:
    """Validate and return cached TMDB show and movie detail responses.

    Each section must use a string TMDB ID as its key and a detail dictionary
    containing the same exact integer ID as its value. Wrong container or ID
    types raise ``TypeError``; a well-typed but mismatched key and ID raises
    ``ValueError``. Both errors include ``cache_path``.
    """
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
    """Split a source title from a final four-digit year in parentheses.

    For example, ``"Doctor Who (2005)"`` becomes ``("Doctor Who", "2005")``.
    Names without that exact trailing pattern are returned unchanged with no
    year. Search uses the title portion while candidate filtering can use the
    year to disambiguate releases.
    """
    match = re.fullmatch(r"(.+) \((\d{4})\)", name)
    if match:
        return match.group(1), match.group(2)
    return name, None


def search_tmdb(aggregated_watch_data: AggregatedWatchData) -> TMDBSearchData:
    """Search TMDB for every supplied show and movie and return all candidates.

    A trailing source year is removed from the query, but the returned mapping
    remains keyed by the original source title. Every result page reported by
    TMDB is requested. The function prints progress and sleeps between requests
    to limit request rate.

    ``TMDB_TOKEN`` must contain a TMDB bearer token. A missing token raises
    ``RuntimeError``; request, response, and unexpected payload errors are
    passed to the caller.
    """
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
    """Extract an unambiguous TMDB ID from a filtered candidate value.

    An ID is returned only for a one-item list containing a dictionary whose
    ``id`` has exactly type ``int``. Empty, ambiguous, malformed, and boolean-ID
    values return ``None`` rather than raising.
    """
    if not isinstance(candidates, list) or len(candidates) != 1:
        return None

    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return None

    tmdb_id = candidate.get("id")
    return tmdb_id if type(tmdb_id) is int and tmdb_id > 0 else None


def is_valid_tmdb_detail(detail: object, tmdb_id: int) -> bool:
    """Check that a detail value is a dictionary for the requested TMDB ID.

    The contained ID must have exactly type ``int``, which prevents boolean IDs
    from being accepted. The function performs no validation of optional detail
    metadata.
    """
    if not isinstance(detail, dict):
        return False
    detail_id = detail.get("id")
    return type(detail_id) is int and detail_id > 0 and detail_id == tmdb_id


def normalize_tmdb_title(title: str) -> str:
    """Normalize Unicode canonical equivalents before exact title comparison.

    NFC normalization makes equivalent composed and decomposed characters
    compare equally. Case, spacing, punctuation, and accents are intentionally
    left unchanged, so matching remains exact in every other respect.

    See https://unicodefyi.com/guide/unicode-normalization-guide/.
    """
    return unicodedata.normalize("NFC", title)


def matches_tmdb_title(
    candidate: Mapping[str, object],
    lookup_title: str,
    title_field: str,
    original_title_field: str,
) -> bool:
    """Check a lookup title against a candidate's primary and original titles.

    ``title_field`` and ``original_title_field`` let the same matcher support TV
    and movie response names. Non-string candidate values are ignored. All
    comparisons use :func:`normalize_tmdb_title` and remain case-sensitive.
    """
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


def matches_tmdb_date(
    candidate: Mapping[str, object], date_field: str, expected_year: str | None
) -> bool:
    """Return whether a candidate's media-specific date starts with a year.

    Shows pass ``first_air_date`` and movies pass ``release_date``. Missing
    years, missing dates, and non-string dates do not match. Full date parsing
    is unnecessary because TMDB dates begin with their four-digit year.
    """
    candidate_date = candidate.get(date_field)
    return bool(
        expected_year
        and isinstance(candidate_date, str)
        and candidate_date[:4] == expected_year
    )


def fetch_details(
    tmdb_search_data: TMDBSearchData, details: TMDBDetailsData
) -> tuple[TMDBDetailsData, list[str]]:
    """Populate a detail cache for titles with exactly one selected candidate.

    ``tmdb_search_data`` is expected to contain filtered candidate lists.
    Existing details with matching IDs are reused. Missing details are fetched
    once per media type and ID, added to the supplied ``details`` dictionary,
    and checkpointed after every five requests. Entries without one valid ID
    remain unresolved and are not treated as request failures.

    The same mutated detail cache and a list of readable failure messages are
    returned. Missing tokens and request or response-validation failures are
    collected instead of raised so all resolvable entries can be attempted.
    Progress and a final summary are printed, and each network attempt is
    followed by the configured request delay. Atomic checkpoint write failures
    propagate immediately after any preceding in-memory updates.
    """
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
                    # Checkpoints limit how much successful network work is lost.
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
    """Add predictable defaults for metadata fields absent from a record.

    Fields listed in ``non_list_fields`` default to ``None`` and fields in
    ``list_fields`` receive independent empty lists. ``setdefault`` preserves
    every existing value, including explicit ``None`` or malformed values. The
    supplied record is mutated and nothing is returned.
    """
    for field in non_list_fields:
        record.setdefault(field, None)
    for field in list_fields:
        record.setdefault(field, [])


def enrich_watch_data(
    aggregated_watch_data: AggregatedWatchData,
    tmdb_search_data: TMDBSearchData,
    tmdb_details: TMDBDetailsData,
) -> None:
    """Enrich generated watch records with allowlisted cached TMDB details.

    Every record first receives stable defaults for its media type. Missing
    watched-episode metadata keys receive ``None``; existing values are
    preserved, but this pipeline does not request TMDB episode details. Records
    with no selected candidate keep their source title and defaults.

    For selected candidates, the function requires a valid cached detail,
    copies only the configured fields, and replaces the source name with a
    non-blank canonical TMDB name or title. It mutates
    ``aggregated_watch_data`` and raises ``RuntimeError`` if a selected ID lacks
    a matching detail entry.
    """
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
    """Fetch and merge search results only for records not already cached.

    Non-empty candidate lists are reused. Missing and empty entries are grouped
    into a smaller aggregate and passed to :func:`search_tmdb`; empty results
    are therefore retried on later runs. The supplied search cache is updated in
    place. If every record is cached, the function returns without requiring a
    token or making a network request. When searching is required, missing-token,
    request, response, and payload errors from :func:`search_tmdb` propagate.
    The cache may already have gained missing media sections through
    ``setdefault`` before such an error.
    """
    media_needing_search: AggregatedWatchData = {"shows": [], "movies": []}

    for media_type in ("shows", "movies"):
        cached_search_results = tmdb_search_data.setdefault(media_type, {})

        for media_record in aggregated_watch_data[media_type]:
            # Empty results are retried because they may reflect a transient search issue.
            if cached_search_results.get(media_record["name"]):
                continue
            if media_type == "shows":
                media_needing_search["shows"].append(cast(ShowWatchData, media_record))
            else:
                media_needing_search["movies"].append(
                    cast(MovieWatchData, media_record)
                )

    # I hate these truthy values.
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
    cached_tmdb_id: int | None = None,
    alternative_titles: dict[int, list[str]] | None = None,
) -> tuple[list[TMDBSearchCandidate], str]:
    """Narrow one title's candidates and explain the matching evidence.

    Only dictionary candidates with positive exact integer IDs are considered.
    Duplicate IDs retain their first result row. A unique direct primary or
    original title match is accepted automatically, subject to an optional source
    year. Every review result retains the full usable candidate list.

    The returned reason describes why the candidate list is trusted or why it
    remains ambiguous. The input list and candidate dictionaries are not
    mutated. ``cached_tmdb_id`` and ``alternative_titles`` are retained for
    callers using the former interface and do not affect cache-first matching.
    """
    valid_search_candidates = _usable_tmdb_candidates(candidates)

    lookup_title, lookup_year = parse_title_and_year(source_title)
    direct_title_matches = [
        candidate
        for candidate in valid_search_candidates
        if matches_tmdb_title(
            candidate, lookup_title, title_field, original_title_field
        )
    ]
    if not direct_title_matches:
        return valid_search_candidates, "no exact title match"

    if lookup_year:
        year_matches = [
            candidate
            for candidate in direct_title_matches
            if matches_tmdb_date(candidate, date_field, lookup_year)
        ]
        if len(year_matches) == 1:
            return year_matches, "exact title and year"
        return valid_search_candidates, "exact title has no unique year match"

    if len(direct_title_matches) == 1:
        return direct_title_matches, "exact title"

    return valid_search_candidates, "exact title is ambiguous"


def _usable_tmdb_candidates(candidates: list[object]) -> list[TMDBSearchCandidate]:
    """Return first candidate rows with distinct positive exact integer IDs."""
    valid_search_candidates: list[TMDBSearchCandidate] = []
    seen_ids: set[int] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = candidate.get("id")
        if type(candidate_id) is not int or candidate_id <= 0:
            continue
        if candidate_id in seen_ids:
            continue
        seen_ids.add(candidate_id)
        valid_search_candidates.append(cast(TMDBSearchCandidate, candidate))
    return valid_search_candidates


def choose_tmdb_match(
    source_title: str,
    media_type: str,
    candidates: list[TMDBSearchCandidate],
    title_field: str,
    original_title_field: str,
    date_field: str,
    reason: str,
) -> TMDBSearchCandidate | None:
    """Ask the user to resolve one TMDB candidate list requiring review.

    Labelled candidate cards with title, date, ID, and an overview preview are
    printed with the reason automatic matching could not decide. The prompt
    repeats until the user enters a valid one-based candidate number or
    ``s``/``skip``. A candidate dictionary is returned for a selection and
    ``None`` means no manual choice was made. The caller leaves the filtered
    candidate list unchanged, so a one-item list can still be used downstream.
    Input exhaustion and numeric conversion errors are not handled specially
    and propagate.
    """
    print(f"Review required: {reason}.")
    print(f"Source {media_type[:-1].title()}: {source_title}")
    print("Select the closest result, or skip.\n")
    for index, candidate in enumerate(candidates, start=1):
        candidate_title = candidate.get(title_field) or "<Unknown>"
        original_title = candidate.get(original_title_field)
        candidate_date = candidate.get(date_field)
        tmdb_id = candidate.get("id")
        overview = " ".join(str(candidate.get("overview") or "<Unknown>").split())
        overview_preview = overview[:117] + "..." if len(overview) > 120 else overview

        print(f"  [{index}] {candidate_title}")
        if original_title and original_title != candidate_title:
            print(f"      Original: {original_title}")
        print(
            f"      Released: {candidate_date or '<Unknown>'}    "
            f"TMDB ID: {tmdb_id if tmdb_id is not None else '<Unknown>'}"
        )
        print(f"      Overview: {overview_preview}\n")

    while True:
        choice = input(
            f"Choose [1-{len(candidates)}], or [s]kip: "
        ).strip()
        if choice.lower() in ("s", "skip"):
            return None
        if choice.isdigit():
            choice_number = int(choice)
            if 1 <= choice_number <= len(candidates):
                return candidates[choice_number - 1]
        print(f"Enter a number from 1 to {len(candidates)}.")


def _load_tmdb_selection_cache() -> TMDBSelectionCache:
    """Load and validate manual TMDB selections, or return an empty cache.

    An existing selection cache is decoded and validated with its project
    relative path. When the cache does not exist, a new empty cache is returned
    without creating a file. Status messages describe which path was taken.
    Cache read and validation errors propagate to the caller.
    """
    if os.path.exists(path_from_project_root(TMDB_SELECTION_CACHE_PATH)):
        print("Selection cache found")
        return validate_tmdb_selection_cache(
            read_tmdb_cache(TMDB_SELECTION_CACHE_PATH), TMDB_SELECTION_CACHE_PATH
        )

    print("No selection cache found")
    return {"shows": {}, "movies": {}}


def _filter_tmdb_search_entry(
    media_type: str,
    source_title: str,
    search_candidates: list[object],
    title_field: str,
    original_title_field: str,
    date_field: str,
    progress_prefix: str,
) -> tuple[list[TMDBSearchCandidate], str]:
    """Filter one uncached source title using direct title and year evidence."""
    filtered_results, reason = filter_tmdb_candidates(
        search_candidates,
        source_title,
        title_field,
        original_title_field,
        date_field,
    )
    discarded_count = len(search_candidates) - len(
        _usable_tmdb_candidates(search_candidates)
    )
    if discarded_count:
        candidate_label = "candidate" if discarded_count == 1 else "candidates"
        print(
            f"Skipping {discarded_count} unusable or duplicate TMDB {candidate_label} "
            f"for {media_type[:-1]} {source_title}."
        )
    print(
        f"{progress_prefix}: filtering left "
        f"{len(filtered_results)} candidates ({reason})."
    )
    return filtered_results, reason


def _review_tmdb_entries(
    tmdb_search_data: TMDBSearchData,
    selection_cache: TMDBSelectionCache,
    review_entries: TMDBReviewEntries,
    processed_entries: int,
) -> None:
    """Resolve review entries and persist successful manual selections.

    Review entries are processed in their existing insertion order. Skipped
    entries become unresolved, and successful selections mutate filtered search
    data before writing the selection cache. Input and write failures propagate
    after any earlier mutations and writes.
    """
    print(f"Entries requiring review: {len(review_entries)}")

    selected_during_review = 0
    skipped_during_review = 0
    for review_index, ((media_type, source_title), review_entry) in enumerate(
        review_entries.items(), start=1
    ):
        search_candidates, reason, review_fields = review_entry
        print(
            f"\nReview [{review_index}/{len(review_entries)}]: "
            f"{media_type[:-1].title()} {source_title}"
        )
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
            print(f"Review skipped for {media_type[:-1]} {source_title}.")
            skipped_during_review += 1
            tmdb_search_data[media_type][source_title] = []
            continue

        tmdb_search_data[media_type][source_title] = [selected_match]
        selected_tmdb_id = selected_match.get("id")
        if type(selected_tmdb_id) is int and selected_tmdb_id > 0:
            selection_cache[media_type][source_title] = selected_tmdb_id
        selected_during_review += 1
        print(
            f"Review selected TMDB ID {selected_tmdb_id} for "
            f"{media_type[:-1]} {source_title}."
        )
        write_json(selection_cache, TMDB_SELECTION_CACHE_PATH)

    print(
        "TMDB filtering complete: "
        f"{processed_entries} entries processed, "
        f"{len(review_entries)} required review, "
        f"{selected_during_review} selected, "
        f"{skipped_during_review} skipped."
    )


def filter_tmdb_search_data(tmdb_search_data: TMDBSearchData) -> None:
    """Resolve TMDB search candidates automatically or through user review.

    Cached positive IDs are selected unconditionally and cached ``None`` values
    remain unresolved. Uncached entries use direct title and optional year
    matching, while every other usable candidate list is reviewed interactively.

    ``tmdb_search_data`` is mutated so each title contains its filtered or
    selected candidates. New manual IDs and no-candidate ``None`` values are
    written atomically to the selection cache. The caller owns persistence of
    the filtered search data itself. Cache-validation, interactive input,
    serialization, and cache-write errors propagate after any preceding
    in-memory mutations.
    """
    selection_cache = _load_tmdb_selection_cache()
    media_type_configs = (
        ("shows", "name", "original_name", "first_air_date"),
        ("movies", "title", "original_title", "release_date"),
    )
    review_entries: TMDBReviewEntries = {}
    total_entries = sum(
        len(tmdb_search_data[media_type]) for media_type, _, _, _ in media_type_configs
    )
    print(f"Filtering {total_entries} TMDB search entries.")
    processed_entries = 0

    for (
        media_type,
        title_field,
        original_title_field,
        date_field,
    ) in media_type_configs:
        for source_title, search_candidates in tmdb_search_data[media_type].items():
            processed_entries += 1
            progress_prefix = (
                f"[{processed_entries}/{total_entries}] "
                f"{media_type[:-1].title()} {source_title}"
            )
            print(f"{progress_prefix}: filtering {len(search_candidates)} candidates.")
            if source_title in selection_cache[media_type]:
                cached_tmdb_id = selection_cache[media_type][source_title]
                if cached_tmdb_id is None:
                    tmdb_search_data[media_type][source_title] = []
                    print(f"{progress_prefix}: unresolved (cached null).")
                    continue
                tmdb_search_data[media_type][source_title] = [{"id": cached_tmdb_id}]
                print(f"{progress_prefix}: accepted cached TMDB ID {cached_tmdb_id}.")
                continue

            filtered_results, reason = _filter_tmdb_search_entry(
                media_type,
                source_title,
                cast(list[object], search_candidates),
                title_field,
                original_title_field,
                date_field,
                progress_prefix,
            )

            tmdb_search_data[media_type][source_title] = filtered_results
            if not filtered_results:
                selection_cache[media_type][source_title] = None
                print(f"{progress_prefix}: unresolved (no usable candidates).")
                write_json(selection_cache, TMDB_SELECTION_CACHE_PATH)
                continue
            if reason not in _AUTOMATIC_MATCH_REASONS:
                review_entries[(media_type, source_title)] = (
                    filtered_results,
                    reason,
                    (title_field, original_title_field, date_field),
                )
                print(f"{progress_prefix}: queued for manual review.")
            else:
                print(f"{progress_prefix}: accepted automatically.")

    _review_tmdb_entries(
        tmdb_search_data,
        selection_cache,
        review_entries,
        processed_entries,
    )
