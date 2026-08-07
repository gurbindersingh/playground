# Playground

This repository is a place to experiment with different languages and tools.

## Code Index

### Bash

| Program | What it does | Concepts used |
|---|---|---|
| `bash/signal-watcher.sh` | Starts, stops, or restarts an application when signal files are present | File-based signaling, conditionals, process control, logging, redirection |
| `bash/trash.sh` | Moves files to a user trash directory and supports listing, pruning, and emptying it | Functions, `getopts`, confirmation prompts, `find`, parameter expansion, safe deletion |
| `bash/restic/` | Runs Restic backups and manages snapshots and retention | Configuration sourcing, environment variables, command composition, exit statuses |
| `bash/mac/backup/` | Orchestrates backups for macOS applications, repositories, files, and cloud storage | `rsync`, exclusion patterns, logging, timestamps, retention, directory management |
| `bash/mac/set-wallpapers.sh`, `themed-wallpapers.sh` | Selects and installs wallpapers based on the current theme and time | Date comparisons, conditionals, path expansion, file operations, logging |
| `bash/mac/rename-to-hash.sh`, `rename-image-to-hash.sh` | Renames files using content hashes while preserving backups and handling collisions | Positional arguments, loops, command substitution, `md5`, `awk`, parameter expansion, `rsync` |
| `bash/mac/convert-webloc-to-url.sh`, `webloc2url.sh` | Extracts URLs from macOS web location files | Text processing, command substitution, file parsing, shell pipelines |
| `bash/mac/battery-status.sh` | Reports macOS battery information | Command execution, output processing, conditionals, formatted output |
| `bash/how-to/` | Provides focused examples for common shell scripting tasks | Quoting, arrays, conditionals, loops, functions, processes, file descriptors, text processing |
| `c/compile.sh` | Compiles and optionally runs the C examples | Argument parsing, flags, shell variables, compiler invocation, exit handling |

### C

| Program | What it does | Concepts used |
|---|---|---|
| `c/ex1.4.c` | Calculates a reduction over an integer array using parallel execution | OpenMP pragmas, parallel regions, thread IDs, reductions, bitwise operations, shared memory |
| `c/parallelfor.c` | Demonstrates parallel loop execution with different scheduling chunk sizes | OpenMP, nested parallel constructs, static scheduling, thread identification, shared state |
| `c/exam2q.c` | Performs a distributed reduction across six MPI processes | MPI initialization, communicators, ranks, process validation, reduce-scatter operations |

### Java

| Program | What it does | Concepts used |
|---|---|---|
| `java/src/fiddles/` | Experiments with filesystem paths, files, regular expressions, control flow, and matrix generation | Java NIO, path normalization, traversal validation, streams, regular expressions, arrays |
| `java/src/leetcode/` | Solves common numeric and data-structure problems | Maps, stacks, loops, string processing, numeric conversion, integer overflow handling |

### Lua

| Program | What it does | Concepts used |
|---|---|---|
| `lua/function.lua` | Processes an options table through a configurable function | Functions, tables, iteration, default configuration patterns, table mutation |

### Python

| Program | What it does | Concepts used |
|---|---|---|
| `python/src/tv_data/` | Converts TV Time CSV exports into an enriched JSON watch library | ETL pipelines, CSV parsing, deduplication, caching, API integration, validation, atomic file writes, testing |
| `python/src/scraper.py` and `python/src/utils/` | Scrapes web pages, extracts useful content, and stores raw and cleaned results | HTTP requests, Beautiful Soup, configuration modules, logging, safe paths, file I/O, delays |
| `python/src/image_hashing.py`, `find-duplicate-hashes.py` | Generates perceptual image hashes and finds duplicate files | Pillow, perceptual hashing, command-line arguments, exception handling, file processing |
| `python/src/world_cities_processor.py` | Extracts, cleans, deduplicates, and sorts city data | File I/O, regular expressions, string transformation, staged processing, progress reporting |
| `python/src/random_word_generator.py` | Generates random words subject to length, repetition, and character-selection rules | Randomness, lists, probability, constraints, command-line input, helper functions |
| `python/src/decode_url.py` | Decodes HTML entities and percent-encoded URLs from the command line | Standard-library modules, URL parsing, command-line arguments, text transformation |
| `python/src/how_to/` | Demonstrates common Python techniques through focused examples | Asyncio, HTTP, HTML, XML, JSON, CSV, plotting, regular expressions, subprocesses, file formats |

### R

| Program | What it does | Concepts used |
|---|---|---|
| `r/retirement_projections.Rmd` | Models salary, pension, savings, investment growth, and projected capital over time | Tidyverse, tibbles, vectorized operations, user-defined functions, financial formulas, data transformation, plotting |

### TypeScript

| Program | What it does | Concepts used |
|---|---|---|
| `web/server/scraper/` | Crawls pages, discovers links, extracts text, and saves raw and cleaned content | Async/await, `Promise.all`, TypeScript types, Cheerio, configuration, file persistence, logging, filtering |
| `web/server/testing-promises.ts` | Demonstrates successful and failed asynchronous operations | `Promise.resolve`, `Promise.reject`, `then`, `catch`, branching, error handling |

### HTML, CSS, and JavaScript

| Program | What it does | Concepts used |
|---|---|---|
| `web/client/download-json.html` | Creates browser data and downloads it as a file | DOM APIs, objects, JSON serialization, Blob URLs, programmatic downloads |
| `web/client/rotate-animation.html` | Rotates an SVG icon when a container is clicked | DOM events, `classList`, CSS transitions, SVG, timers, UI state |
