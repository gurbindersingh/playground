#!/usr/bin/env bash
set -e

# Bash concatenates strings when they don't have a space between them
string="Hel""lo"
echo "$string"

# We can use that to nest strings
string='"'"$string"'" world'
echo "$string"

# What does the string above do exactly?
# It consists of three segments that are concatenated together:
# 1. '"' -> this is single quoted string that contains only the double-quote character.
# 2. "$string" -> since a single-quoted string does not expand variables, we use a double-quoted segment.
# 3. '" world' -> again a single quoted segment.
