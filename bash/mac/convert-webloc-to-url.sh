#!/usr/bin/env bash
set -e

log_file="$HOME/logs/convert-webloc.log"
script_directory="$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck source=configs/links.sh
source "$script_directory/configs/links.sh"

{
  find "$links_directory" -type f -iname '*.webloc' | while read -r file; do
    # Extract the URL from the webloc file.
    url=$(/opt/homebrew/bin/rg --no-line-number --trim '<string>.+</string>' "$file" | sed -E 's/<(\/)?string>//g')
    # Replace the suffix of the file
    url_file="${file/%webloc/url}"
    
    echo "[InternetShortcut]" > "$url_file"
    echo "URL=$url" >> "$url_file"
    
    echo "[$(date +'%F %H:%M:%S')] Converted $file"
    mv "$file" "$HOME/.trash-bin"
  done
  echo "[$(date +'%F %H:%M:%S')] DONE"
} >> "$log_file" 2>&1
