#!/usr/bin/env bash
set -e

# The trick is the ' %f' format directive. It prints only the file name.
find path1/ path2/ -type f -printf '%f\n' | sort | uniq -d

# If the paths are nested use a max depth
find path1/ path1/path2/ -maxdepth 1 -type f -printf '%f\n' | sort | uniq -d
