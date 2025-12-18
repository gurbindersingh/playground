#!/usr/bin/env bash
set -e

echo "[$(date +'%F %H:%M:%S')] Backing up files"

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

. ./configs/files.sh

{
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
