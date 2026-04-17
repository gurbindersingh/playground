#!/usr/bin/env bash
set -e

# Different ways to feed multiple inputs into an operation and process each
# one individually. Most examples use finding .jpg files and renaming each to
# its SHA-256 hash as the running use case. Snippets work both interactively
# and in scripts; key differences are noted per section.
#
# Interactive vs. script differences:
#   - set -e: scripts commonly run with it (any non-zero exit aborts);
#     interactive shells rarely do, so errors just print and execution
#     continues. Guard commands that may legitimately return non-zero with
#     `|| true` in scripts.
#   - Subshell variable scope: in scripts you often accumulate state across
#     loop iterations (counters, arrays) — a piped while-read loop loses that
#     state because the body runs in a subshell. Use process substitution
#     instead. Interactively this rarely matters.
#   - Shell options (shopt): may already be active in an interactive shell via
#     ~/.bashrc; scripts must set them explicitly before use.
#
# shasum -a 256 outputs "<64-hex-chars>  <path>"; awk '{print $1}' or cut -d "
# " -f1 extracts just the hash. ${f##*.} strips everything up to and including
# the last dot → extension. mv -- treats -- as end-of-options, guarding against
# filenames starting with -.

# =============================================================================
# FOR LOOPS — inputs known upfront (globs, arrays, literal lists)
# =============================================================================
# The shell expands the full list BEFORE the loop starts. This makes for loops
# simple and subshell-free: variables set inside persist after the loop ends.
#
# Do NOT use `for f in $(cmd)` when items may contain spaces — the command
# output is word-split on IFS before iteration, breaking on any whitespace in
# filenames. Use a while-read loop for command output instead.
#
# Preferred for scripts: same glob approach as interactive, but set any
# required shopt options (nullglob, globstar) explicitly at the top of the
# script — they may already be active in an interactive shell via ~/.bashrc
# but scripts start with a clean environment.

# --- for loop with glob ---
# Simplest approach: no external tools, shell handles expansion.
# Current directory only, does not recurse into subdirectories.
# Caveat: if no files match and nullglob is off (bash default), the loop runs
# once with f='*.jpg' (the literal pattern). Add [[ -f "$f" ]] || continue
# inside the loop, or run shopt -s nullglob first.
for f in *.jpg; do mv -- "$f" "$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Recursive variant using globstar. Requires shopt -s globstar in bash;
# globstar is enabled by default in zsh.
shopt -s globstar
for f in **/*.jpg; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# mapfile/readarray: reads all command output into an array upfront, then
# iterates with a for loop. Avoids both the subshell issue of piped while-read
# and the need for process substitution. More useful in scripts than
# interactively — in a script, collecting into an array first lets you inspect
# or validate the full list before acting on it.
# Requires bash 4+ (not available in bash 3.2, which is the default on macOS,
# or in sh).
mapfile -t files < <(find . -name "*.jpg")
for f in "${files[@]}"; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# =============================================================================
# WHILE LOOPS — inputs come from a command's output, one line at a time
# =============================================================================
# Unlike for loops, while-read processes output line by line, making it safe
# for items with spaces (with IFS=''). read -r prevents backslash sequences
# in filenames from being interpreted as escape characters.
#
# Subshell caveat: when the source is piped in (cmd | while), the loop body
# runs in a subshell — variables set inside are lost after the loop ends. To
# preserve variables, use process substitution: `while ...; done < <(cmd)`.
#
# Preferred for scripts: null-delimited process substitution — avoids the
# subshell so accumulated state (counters, arrays) is visible after the loop,
# and handles filenames containing newlines safely.

# --- while read with pipe ---
# Readable and idiomatic. Fine interactively where accumulated state rarely
# matters. Main caveats:
#   - The loop body runs in a subshell; variables set inside are lost after.
#     In scripts, use process substitution instead if state must persist.
#   - Breaks on filenames containing newlines; use the null-delimited variant below.
find . -name "*.jpg" | while IFS='' read -r f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Process substitution variant: avoids the subshell — the loop body runs in the
# current shell, so variables set inside persist after the loop ends. Preferred
# over the pipe variant in scripts where state must survive the loop.
# Caveat: process substitution requires bash or zsh; not available in POSIX sh.
while IFS='' read -r f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done < <(find . -name "*.jpg")

# Null-delimited variant: -print0 outputs NUL-terminated paths; read -r -d ''
# reads until NUL, safe for any filename including those containing newlines.
# Subshell caveat from above still applies.
find . -name "*.jpg" -print0 | while IFS='' read -r -d '' f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Null-delimited process substitution: combines both — no subshell and safe for
# filenames containing newlines. The most complete while-read variant; most
# useful in scripts where avoiding the subshell matters (e.g. a counter or
# accumulator variable set inside must be visible after the loop).
while IFS='' read -r -d '' f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done < <(find . -name "*.jpg" -print0)

# Arbitrary pipeline as source: the input doesn't have to come from find — any
# command whose output is one item per line works. Here: find files whose
# <prefix>.<name>.<ext> prefix appears more than once, then move the first
# match for each duplicate prefix to a target directory.
# `grep -m1` stops after the first match — no need for `head -1`.
# Spaces in filenames are not an issue: ls -1 outputs one filename per line
# regardless of spaces, and IFS='' read -r reads the whole line without
# splitting — so a prefix like "my file" is passed intact. This is why
# `for prefix in $(cmd)` would break here but `while read` does not.
# Subshell caveat from above still applies.
# Caveat: if a prefix contains regex metacharacters (e.g. `+`, `[`), the grep
# pattern may misbehave — in practice prefixes are plain alphanumeric strings.
# Script caveat: grep exits with code 1 when there is no match; with set -e
# active this would abort the script. Guard with `grep ... || true` if running
# as a script. Interactively, set -e is rarely active so this is not an issue.
ls -1 | sort | awk -F '.' '{print $1}' | uniq -d | while IFS='' read -r prefix; do first=$(ls -1 | sort | grep -m1 "^${prefix}\."); mv -- "$first" /path/to/target/; done

# =============================================================================
# FIND -EXEC AND XARGS — let the tool handle iteration
# =============================================================================
# These avoid shell loop syntax entirely: find or xargs handles the iteration.
# Equally suited to interactive and script use. Preferred when find's filtering
# options (-mtime, -size, -type, etc.) are needed, or when parallel execution
# (xargs -P) is desired.
#
# Preferred for scripts: -exec + or xargs (batched) over -exec \; — spawning
# one process per file is correct but slow on large sets.

# --- find -exec with \; ---
# sh is used instead of bash for portability (bash is absent on many minimal
# systems) and startup speed (on Linux /bin/sh is usually dash, which starts
# faster than bash — relevant when -exec \; spawns one process per file).
# The inline scripts use only POSIX sh features, so bash is not needed.
# find calls execv(sh, [sh, -c, SCRIPT, _, FILE]) for each match.
# _ is the dummy $0; the matched path lands in $1.
# cut -d " " -f1 is used here instead of awk because single quotes are
# unavailable inside the sh -c '...' string; passing space as a separate
# argument to cut (-d followed by " ") is POSIX-valid.
# Spawns one sh process per file, correct but slow on large sets.
find . -name "*.jpg" -exec sh -c 'mv -- "$1" "$(dirname "$1")/$(shasum -a 256 "$1" | cut -d " " -f1).${1##*.}"' _ {} \;

# --- find -exec with + ---
# Batches all matched paths into as few sh invocations as possible, much faster.
# for f is shorthand for for f in "$@"; iterates all positional args safely.
# If total args exceed ARG_MAX (~2 MB on macOS), find splits into multiple batches.
find . -name "*.jpg" -exec sh -c 'for f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | cut -d " " -f1).${f##*.}"; done' _ {} +

# --- xargs -I{} ---
# xargs replaces {} with the filename. {} is placed after the script string, not
# inside it, so xargs text substitution never touches the script; the filename
# reaches $1 as a proper argument regardless of spaces or special characters.
# -I{} processes one file per invocation (no batching benefit over -exec \;).
# The main reason to prefer xargs is the -P flag for parallel execution (below).
# Caveat: on some older BSD xargs, -I may override the null-delimiter behavior
# of -0; test portability if targeting non-macOS systems.
find . -name "*.jpg" -print0 | xargs -0 -I{} sh -c 'mv -- "$1" "$(dirname "$1")/$(shasum -a 256 "$1" | cut -d " " -f1).${1##*.}"' _ {}

# Parallel variant with xargs -P: runs up to 4 sh processes concurrently.
# mv is a kernel-level rename syscall and is atomic per file, so parallel
# execution is safe. If you add echo statements, output lines from concurrent
# processes may interleave.
find . -name "*.jpg" -print0 | xargs -0 -P4 -I{} sh -c 'mv -- "$1" "$(dirname "$1")/$(shasum -a 256 "$1" | cut -d " " -f1).${1##*.}"' _ {}

# --- General caveats ---
# Filenames with spaces are safe as long as variables are double-quoted ("$f", "$1").
# Filenames containing newlines are only safe with null-delimited variants.
# Files without an extension: ${f##*.} returns the full basename, so the renamed
# file becomes <hash>.<fullbasename>, probably not what you want.
# If shasum fails (e.g. unreadable file), awk/cut outputs nothing and mv silently
# tries to rename the file to .<ext>, there is no built-in error propagation.
