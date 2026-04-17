# Example showing how rename each matched file to its SHA-256 hash, preserving
# the extension. Example: photo.jpg → e3b0c442...b855.jpg
#
# shasum -a 256 outputs "<64-hex-chars>  <path>"; awk '{print $1}' or cut -d "
# " -f1 extracts just the hash. ${f##*.} strips everything up to and including
# the last dot → extension. mv -- treats -- as end-of-options, guarding against
# filenames starting with -.

# --- for loop with glob ---
# Shell expands *.jpg before the loop starts; no external tool needed.
# Current directory only, does not recurse into subdirectories.
# Caveat: if no files match and nullglob is off (bash default), the loop runs
# once with f='*.jpg' (the literal pattern). Add [[ -f "$f" ]] || continue
# inside the loop, or run shopt -s nullglob first.
for f in *.jpg; do mv -- "$f" "$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Recursive variant using globstar. Requires shopt -s globstar in bash;
# globstar is enabled by default in zsh.
shopt -s globstar
for f in **/*.jpg; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

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

# --- while read with pipe ---
# Readable and idiomatic. Main caveats:
#   - The loop body runs in a subshell; variables set inside are lost after.
#   - Breaks on filenames containing newlines; use the null-delimited variant below.
# read -r prevents backslash interpretation in filenames.
find . -name "*.jpg" | while read -r f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# Null-delimited variant: -print0 outputs NUL-terminated paths; read -r -d ''
# reads until NUL, safe for any filename, including those containing newlines.
# Subshell caveat from above still applies.
find . -name "*.jpg" -print0 | while read -r -d '' f; do mv -- "$f" "$(dirname "$f")/$(shasum -a 256 "$f" | awk '{print $1}').${f##*.}"; done

# --- xargs -I{} ---
# xargs replaces {} with the filename. {} is placed after the script string, not
# inside it, so xargs text substitution never touches the script, the filename
# reaches $1 as a proper argument regardless of spaces or special characters.
# -I{} processes one file per invocation (no batching benefit over -exec \;).
# The main reason to prefer xargs is the -P flag for parallel execution (below).
# Caveat: on some older BSD xargs, -I may override the null-delimiter behavior
# of -0, test portability if targeting non-macOS systems.
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
