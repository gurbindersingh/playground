#!/usr/bin/env bash
set -e

filename="somefile.ext"
# https://cheatsheets.zip/bash#bash-parameter-expansions
echo "${filename##*.}"
