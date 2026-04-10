#!/usr/bin/env bash
set -e

# Demos several stdin-reading techniques end-to-end. Because stdin can only
# be consumed once, we stash the input in a temp file up front and feed each
# block from it.
if [ -t 0 ]; then
  echo "usage: printf 'a\\nb\\nc' | $0" >&2
  exit 1
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
cat > "$tmp"

# --- 1. Slurp everything into a variable with `cat` ---------------------------
# Gotcha: command substitution strips ALL trailing newlines, so `"$input"`
# won't round-trip input that ends in blank lines.
{ input=$(cat); echo "1: $input"; } < "$tmp"

# --- 2. Same thing without spawning `cat` -------------------------------------
# Faster (no subprocess). Gotcha: same trailing-newline stripping as #1. Also,
# `$(<file)` only works on real files — NOT on process substitution `<(cmd)`.
{ input=$(</dev/stdin); echo "2: $input"; } < "$tmp"

# --- 3. Read a single line ----------------------------------------------------
# `-r`  : don't treat backslashes as escapes (otherwise `\n` etc. get mangled).
# `IFS=`: don't strip leading/trailing whitespace from the line.
# Gotcha: `read` returns non-zero on EOF, which trips `set -e` — guard it.
{ IFS= read -r line || true; echo "3: $line"; } < "$tmp"

# --- 4. Line-by-line loop -----------------------------------------------------
# Gotcha A: a final line with no trailing `\n` is silently dropped unless you
#           add `|| [[ -n $line ]]`.
# Gotcha B: `cmd | while read ...` runs the loop body in a subshell, so any
#           variables set inside are lost. Use input redirection instead:
#           `while ...; done < <(cmd)`  or  `done < file`.
while IFS= read -r line || [[ -n $line ]]; do
  echo "4: $line"
done < "$tmp"

# --- 5. Read all lines into an array ------------------------------------------
# Gotcha: `readarray`/`mapfile` DO NOT EXIST on macOS's default /bin/bash (3.2),
# so only use the builtin when we're on bash 4+. Otherwise fall back to the
# portable `while read` loop — we deliberately run only the branch that
# actually works on the current shell.
if ((BASH_VERSINFO[0] >= 4)); then
  readarray -t lines < "$tmp" # or: mapfile -t lines < "$tmp"
else
  lines=()
  while IFS= read -r line || [[ -n $line ]]; do
    lines+=("$line")
  done < "$tmp"
fi
printf '5: %s\n' "${lines[@]}"

# --- 6. NUL-delimited input (safe for filenames with newlines/spaces) ---------
# Pair with producers that emit NULs: `find -print0`, `grep -Z`, `xargs -0`.
# Gotcha: `-d ''` expects real NUL bytes. Feeding newline-delimited data to a
# `-d ''` loop will slurp the whole stream into one `$item`.
while IFS= read -r -d '' item; do
  echo "6: $item"
done < <(printf '%s\0' one two "three with spaces")

# --- 7. Detect piped/redirected stdin vs an interactive terminal --------------
# Useful for scripts that should either read from a pipe or prompt the user.
# Gotcha: `-t 0` only tells you whether fd 0 is a TTY. It does NOT tell you
# whether data is actually waiting — a slow producer still looks "piped"
# before any bytes arrive, so don't use this as a "has input ready" check.
if [ ! -t 0 ]; then
  input=$(cat)
  echo "7: piped — got '$input'"
else
  read -rp "Enter value: " input
  echo "7: interactive — got '$input'"
fi < "$tmp"
