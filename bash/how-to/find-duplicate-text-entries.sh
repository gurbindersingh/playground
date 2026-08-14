#!/usr/bin/env bash
set -e

text="
foo
bar
baz
foo
"

# With the -d option we can only print the entries that appear more than once.
# But uniq can only detect consecutive duplicates, so the input needs to be
# sorted first.
echo "$text" | sort | uniq -d
