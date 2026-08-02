# TV Data Conversion

The `tv_data` package converts TV Time CSV exports into a single JSON watch
library and enriches shows and movies with metadata from
[The Movie Database (TMDB)](https://www.themoviedb.org/).

The conversion is a batch process. It reads files from `data/tvtime`, writes
intermediate snapshots and caches, may ask the user to resolve ambiguous TMDB
matches, and regenerates `data/tvtime/watch_data_final.json` when successful.

## Running the Pipeline

Run the module from the Python project root with `src` on the import path:

```bash
TMDB_TOKEN="your-tmdb-bearer-token" PYTHONPATH=src python -m tv_data.main
```

The project requires Python 3.13 or newer and its declared dependencies,
including `requests`, must already be installed.

`TMDB_TOKEN` is required whenever uncached search or detail requests are needed.
Alternative-title matching simply has no additional evidence when the token is
missing, but missing search or detail data cannot be fetched.

The command needs:

- The expected TV Time CSV files under `data/tvtime`.
- Write access to `data/tvtime` for snapshots and caches.
- Network access when required TMDB data is not cached.
- An interactive terminal when a nonempty candidate list requires review.

The package has no registered project script or `tv_data.__main__` module. The
supported module invocation is `python -m tv_data.main`.

## Input Files

`main.py` reads these show exports in order:

1. `data/tvtime/tracking-prod-records-v2.csv`
2. `data/tvtime/show_seen_episode_latest.csv`
3. `data/tvtime/followed_tv_show.csv`
4. `data/tvtime/seen_episode_latest.csv`
5. `data/tvtime/tracking-prod-records.csv`
6. `data/tvtime/user_tv_show_data.csv`

Movie rows are also read from:

```text
data/tvtime/tracking-prod-records.csv
```

The exports use more than one pair of episode columns. Show aggregation accepts
both `s_no`/`ep_no` and `season_number`/`episode_number`.

All six show files and the movie file are opened unconditionally and read fully
into memory as UTF-8 CSV. Invalid nonblank season or episode numbers stop the
conversion during integer parsing. A watched episode also requires an
`updated_at` column. File, decoding, and CSV errors propagate. Most optional
columns use `.get()` and a missing header is treated as absent. An imported
episode directly accesses the `updated_at` key, so that missing header raises;
a blank value is not validated.

Names are trimmed before indexing. Missing or whitespace-only show and movie
names are skipped and reported with their source file and CSV row number.

TV Time timestamps are compared as sortable strings. They are not parsed as
datetime objects. Records start with `9999-99-99 99:99:99` for `created_at` and
`0000-00-00 00:00:00` for `updated_at`; missing or blank source timestamps can
leave these sentinels in generated output. Otherwise, show and movie records
retain their earliest `created_at`, and movies retain their latest `updated_at`.
A show's `updated_at` changes when the row timestamp is nonblank and at least as
new as the stored value, and the raw archive column is truthy. Whitespace alone
is truthy before trimming and therefore updates the timestamp while setting
`is_archived` to false. Only archive values `true` and `1`, ignoring case and
surrounding whitespace, mean archived.

## Pipeline Stages

The command performs these stages in order:

1. Aggregate each show CSV into a title-keyed dictionary.
2. Sort each show's watched episodes by season and episode number.
3. Aggregate movies into a title-keyed dictionary.
4. Flatten the show and movie dictionaries into JSON lists.
5. Deduplicate watched episodes.
6. Load or fetch raw TMDB search candidates.
7. Filter candidates automatically and interactively.
8. Load or fetch TMDB show and movie details.
9. Add allowlisted TMDB metadata to generated records.
10. Write the final snapshot and stable final path.

A numbered `watch_data_<n>.json` snapshot is written after each CSV aggregation
and major conversion stage. These files make it possible to inspect how data
changes throughout a run. Consumers should not assume that a particular stage
always has the same snapshot number because changing the pipeline can change
the numbering. Snapshots are overwritten progressively and old later-stage
files are not removed. If a run fails, the directory can contain early
snapshots from the failed run and later snapshots from an older run.

`watch_data_final.json` is a stable path to the latest successfully generated
result. It is not an input or merge target. Every successful run replaces it,
so manual edits to that file are lost.

All package JSON writes use a temporary file in the destination directory,
flush it to disk, and replace the destination with `os.replace`. This prevents
a serialization or pre-replacement write failure from truncating an existing
cache or output file. It does not lock files against concurrent writers.

## Episode Deduplication

An episode is identified by its `(season, episode)` pair.

- Duplicate pairs keep the entry with the greatest `updated_at` string.
- Equal timestamps keep the first encountered entry.
- The placeholder pair `(0, 0)` is removed.
- A missing season number is imported as `-1`.
- The cleaned list is returned in ascending season and episode order.

The generated schema does not contain TV Time's reported `ep_watch_count`.
Watched state comes from the concrete entries in `episodes_watched`.

## TMDB Cache Files

The pipeline separates raw API results, filtered matches, manual decisions, and
detail responses:

| File | Purpose |
| --- | --- |
| `tmdb_search_data.json` | Raw search candidates returned by TMDB. |
| `tmdb_search_data_filtered.json` | Candidates remaining after automatic and manual filtering. |
| `tmdb_selection_cache.json` | Source-title to TMDB-ID choices made during interactive review. |
| `tmdb_details.json` | ID-keyed show and movie detail responses used for enrichment. |

All paths are under `data/tvtime`.

### Raw Search Cache

On startup, an existing raw search cache is decoded and validated. Non-empty
candidate lists are reused. Current input titles that are missing or have empty
lists are searched again, which allows a later run to recover from a previous
empty result. Cached titles absent from the current CSV library are never
pruned. They are still filtered and processed for details along with current
titles, so a stale entry can cause review, requests, or a detail failure in a
later run.

The raw cache is written before filtering begins. Filtering then changes the
in-memory candidate lists and writes those reduced lists to the filtered cache.
The filtering function does not rewrite the raw cache. New search results are
not checkpointed while pagination or other titles are still being fetched. If
that search call fails, its accumulated results are not merged or persisted.

The filtered cache is an output for inspection and is never loaded by the
pipeline. It is replaced only after filtering and review complete. If that
stage stops early, an older filtered file can remain beside a newer raw cache.

### Selection Cache

Interactive choices with integer TMDB IDs are stored separately. A candidate
without an integer ID can be chosen, but no ID is added to the cache and detail
processing cannot use that choice. A cached choice is considered during future
filtering. If its current direct title or optional year does not agree with the
source title, it remains subject to review rather than being trusted silently.

The cache file is written immediately after each manual choice, so valid ID
choices already made survive if the process stops. Existing entries are never
pruned when titles disappear from the CSV library.

### Detail Cache

Detail fetching only considers titles with exactly one candidate containing an
integer ID. A valid existing detail is reused. Missing details are fetched once
per media type and ID, even when multiple source titles select that ID.

The detail cache is checkpointed after every five network requests and written
again by `main()` after fetching finishes. Request failures are collected and
reported. Missing-token detail failures are collected without making a request.
If any detail fetch failed, `main()` stops before final enrichment. Titles
without a selected ID are unresolved rather than failed. If the pipeline reaches
enrichment, those records receive metadata defaults. Existing detail entries
are never pruned.

## Cache Validation

JSON decoding does not prove that a cache has the shape required by the
application. The package validates persisted caches when reading them:

- Every cache must be a JSON object with object-valued `shows` and `movies`.
- Search-cache titles must map to candidate lists.
- Selection-cache titles must map to exact integer IDs; booleans are rejected.
- Detail entries must have string ID keys matching exact integer IDs inside the
  detail objects.

Malformed cache roots and sections, selection IDs, or detail mappings stop the
command with an error naming the affected cache. Search candidate entries and
their IDs are different: non-object candidates are skipped and reported, while
object candidates are not rejected solely for a missing or malformed ID.

The `TypedDict` declarations in `models.py` help static type checkers understand
the expected structures. They do not perform runtime validation and do not
change values decoded by `json.load`.

## Candidate Matching

TV and movie search responses use different field names, but follow the same
matching process.

1. A final source suffix in the exact form ` (YYYY)`, including the preceding
   literal space, is separated from the title.
2. Primary and original TMDB titles are compared with the source title.
3. A candidate whose ID equals the cached manual ID is checked against its
   current direct title and optional year. A compatible match wins; a conflict
   is sent to review before ordinary year narrowing.
4. When there is no decisive cached match and the first pass reports exactly
   `no exact title match`, alternative titles may be fetched and compared.
5. If the source supplied a year, `first_air_date` or `release_date` narrows the
   remaining title matches.
6. Ambiguous, conflicting, or unverified results are presented for review.

Title comparison applies Unicode NFC normalization so canonically equivalent
Unicode text compares equally. It does not lowercase, trim, remove accents, or
normalize punctuation. Matching is otherwise exact.

Malformed search entries that are not JSON objects are removed before any
candidate field is accessed. Object candidates can still lack expected fields;
missing values appear as unknown during interactive review.

Alternative titles are cached only in memory for one filtering run. They are
not persisted, so an eligible candidate can require the same request again on a
later run. Requests still require an integer candidate ID, `TMDB_TOKEN`, and a
first-pass reason of exactly `no exact title match`.

## Interactive Review

When automatic matching cannot trust a result, the command prints each
candidate's primary title, original title, date, ID, and overview. Enter the
one-based candidate number to select it. Entering `s` or `skip` records no
manual choice, but the caller leaves the filtered candidate list unchanged. If
that list contains exactly one integer-ID candidate, detail fetching can still
treat it as selected. This is a known limitation rather than a reliable way to
force an unresolved result.

The prompt repeats after ordinary invalid input. End-of-file and some unusual
Unicode numeric input can propagate an input or integer conversion error.

## Metadata Enrichment

Only explicitly allowlisted fields are copied from TMDB details. This avoids
making the generated schema depend on every field returned by the API.

Matched records receive TMDB IDs, dates, artwork paths, overviews, ratings,
status information, genres, and media-specific fields when available. Their
source names are replaced with nonblank canonical TMDB names or titles.

Unmatched records keep their source names. Missing scalar metadata fields are
set to `null`, and missing list metadata fields are set to separate empty lists.
Existing values are preserved when defaults are applied.

Watched episode objects receive these optional metadata keys:

- `name`
- `overview`
- `air_date`
- `runtime`
- `still_path`
- `vote_average`
- `vote_count`

The pipeline does not call TMDB season or episode detail endpoints. Missing
episode metadata therefore remains `null`; only pre-existing values are
preserved.

## Network Behavior

TMDB requests use a 30-second timeout and wait one third of a second after
handled responses or detail attempts. Search retrieves every page reported by
TMDB. There is no retry, exponential backoff, page limit, or cross-process rate
limiter.

Search and detail requests use the bearer token from `TMDB_TOKEN`. HTTP errors,
invalid search payloads, and cache checkpoint write errors can stop the command.
Alternative-title request errors are reported and treated as no matching
evidence so filtering can continue.

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `main.py` | Runs the ordered pipeline and writes snapshots, raw/filtered search caches, the final detail cache, and final output. |
| `tv_data.py` | Reads CSV exports and aggregates, sorts, and deduplicates watch data. |
| `tmdb.py` | Validates caches, calls TMDB, matches candidates, checkpoints details, persists selections, and enriches records. |
| `file_utils.py` | Reads project-relative JSON and performs atomic JSON replacement. |
| `models.py` | Defines static dictionary shapes for generated data and caches. |

Function docstrings contain the detailed contract for each operation, including
whether it mutates an argument, performs I/O, or propagates errors.

## Known Limitations

- Input filenames and snapshot/final paths are fixed in `main.py`; TMDB cache
  paths are fixed in `tmdb.py`.
- A terminal is required for review entries with nonempty candidate lists.
- Empty TMDB search results for current input titles are retried on every run.
- Raw, selection, and detail caches retain titles no longer present in the CSV
  library.
- The filtered cache is write-only and can be stale after an interrupted run.
- Search pagination and alternative-title requests have no retry or upper bound.
- Episode-level TMDB metadata is not fetched.
- Cache writes are atomic but are not protected by process locking.
- Atomic replacement does not synchronize the destination directory, so it is
  not guaranteed durable across a system crash immediately after replacement.
- A malformed object candidate without an ID can interact incorrectly with an
  absent cached selection because both ID values are `None`.
- `skip` does not clear a reviewed candidate list, so one remaining candidate
  can still be used downstream.
