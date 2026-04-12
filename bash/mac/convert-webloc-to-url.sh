#!/usr/bin/env bash
set -e

log_file="$HOME/logs/convert-webloc.log"

{
  config="${XDG_CONFIG_HOME:-$HOME/.config}/convert-webloc-to-url.sh"
  [ -r "$config" ] || {
    echo "Config not found: $config" >&2
    exit 1
  }
  # shellcheck source=/dev/null
  . "${config}"

  find "${links_directory:?}" -type f -iname '*.webloc' | while read -r file; do
    webloc2url "$file"
    echo "[$(date +'%F %H:%M:%S')] Converted $file"
    mv "$file" "$HOME/.trash-bin"
  done
  echo "[$(date +'%F %H:%M:%S')] DONE"
} >>"$log_file" 2>&1
