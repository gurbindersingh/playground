#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. configs/firefox.sh

source="$HOME/Library/Application Support/Firefox/Profiles"
repo="$HOME/${dest:?}/backup"

# NOTE: Change into the source directory so that changes to the metadata in
#       the parent directories does not trigger a snapshot.
cd "$source"
echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '$dest'"
restic backup --insecure-no-password --repo "$repo" --skip-if-unchanged ./
echo "[$(date +'%F %H:%M:%S')] DONE"
echo "============================================================================="
echo ""
# NOTE:
#   - List snapshots: restic snapshots --insecure-no-password --repo REPO
#   - List files: restic ls SNAPSHOT_ID --insecure-no-password --repo REPO

restic --insecure-no-password forget \
  --prune \
  --keep-daily 30 \
  --keep-weekly 24 \
  --repo "$repo"

restic --insecure-no-password --repo "$repo" check
