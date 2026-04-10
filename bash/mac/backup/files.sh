#!/usr/bin/env bash
set -e

echo "[$(date +'%F %H:%M:%S')] Backing up files"

{
  config="${XDG_CONFIG_HOME:-$HOME/.config}/files-backup.sh"
  [ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
  . "$config"

  echo "[$(date +'%F %H:%M:%S')] Creating backup of '${source:?Source not set}' at '${dest:?Destination not set}'."
  rsync -av \
    --exclude=".tmp.drive*" \
    --exclude=".idea" \
    --exclude="target" \
    --exclude="*.ini" \
    --exclude="node_modules" \
    --exclude=".venv" \
    "$source" "$dest"

  echo ""
  echo "============================================================================="
  echo ""
} >>"$HOME/logs/files.backup.log" 2>&1
