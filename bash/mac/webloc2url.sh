#!/usr/bin/env bash
set -e

if [[ $# -le 0 ]]; then
  echo "Missing FILE argument."
  echo "Usage: $(basename "$0") FILE..."
  exit 1
fi

files=("$@")

for file in "${files[@]}"; do
  # Extract the URL from the webloc file.
  url=$(/opt/homebrew/bin/rg --no-line-number --trim '<string>.+</string>' "$file" | sed -E 's/<(\/)?string>//g')
  [ -n "$url" ] || {
    echo "No URL found in file. Is it a .webloc file?"
    exit 1
  }
  # Replace the suffix of the file
  url_file="${file/%webloc/url}"

  echo "[InternetShortcut]" >"$url_file"
  echo "URL=$url" >>"$url_file"
done
