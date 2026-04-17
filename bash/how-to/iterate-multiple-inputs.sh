#!/usr/bin/env bash
set -e

# Different ways to feed multiple inputs into an operation and process each
# one individually. Most examples use finding .jpg files and renaming each to
# its SHA-256 hash as the running use case.
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

# --- while read with pipe ---
# Readable and idiomatic. Main caveats:
#   - The loop body runs in a subshell; variables set inside are lost after.
#   - Breaks on filenames containing newlines; use the null-delimited variant below.
find . -name "*.jpg" | while IFS='' read -r f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Process substitution variant: avoids the subshell — the loop body runs in the
# current shell, so variables set inside persist after the loop ends.
# Caveat: process substitution requires bash or zsh; not available in POSIX sh.
while IFS='' read -r f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done < <(find . -name "*.jpg")

# Null-delimited variant: -print0 outputs NUL-terminated paths; read -r -d ''
# reads until NUL, safe for any filename including those containing newlines.
# Subshell caveat from above still applies.
find . -name "*.jpg" -print0 | while IFS='' read -r -d '' f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Arbitrary pipeline as source: the input doesn't have to come from find — any
# command whose output is one item per line works. Here: find files whose
# <prefix>.<name>.<ext> prefix appears more than once, then move the first
# match for each duplicate prefix to a target directory.
# `grep -m1` stops after the first match — no need for `head -1`.
# Subshell caveat from above still applies.
# Caveat: if a prefix contains regex metacharacters (e.g. `+`, `[`), the grep
# pattern may misbehave — in practice prefixes are plain alphanumeric strings.
ls -1 | sort | awk -F '.' '{print $1}' | uniq -d | while IFS='' read -r prefix; do first=$(ls -1 | sort | grep -m1 "^${prefix}\."); mv -- "$first" /path/to/target/; done

# =============================================================================
# FIND -EXEC AND XARGS — let the tool handle iteration
# =============================================================================
# These avoid shell loop syntax entirely: find or xargs handles the iteration.
# Preferred when find's filtering options (-mtime, -size, -type, etc.) are
# needed, or when parallel execution (xargs -P) is desired.

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
