#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

if [[ "$#" -lt 2 ]]; then
  echo "Missing parameter(s)"
  echo "Usage: sync SRC DEST"
  echo "  NOTE: Paths should not containing a trailing slash."
  exit 1
fi

source="$1"
destination="$2"
timestamp="$(date +'%F_%H%M.%S')"
backup_dir="$destination.changed/$timestamp"

echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '$destination'."
echo "[$(date +'%F %H:%M:%S')] Changed and deleted files be saved at '$backup_dir'."

# NOTE: Incremental backups do not work on some file systems, like exFAT.
#       So instead we use the `--backup-dir` feature to create an archive
#       of deleted and changed files.
rsync -avb \
  --backup-dir="$backup_dir" \
  --delete-after \
  --exclude=".git" \
  --exclude=".tmp.drive*" \
  --exclude=".idea" \
  --exclude=".vscode" \
  --exclude="target" \
  --exclude="*.ini" \
  --exclude="Sync.Cache" \
  --exclude=".DS_Store" \
  "$source" "$destination"

echo "[$(date +'%F %H:%M:%S')] DONE"
echo ""
