#!/usr/bin/env bash
set -e

echo "[$(date +'%F %H:%M:%S')] Backing up Thunderbird profiles"

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. configs/thunderbird.sh

# NOTE: Change into the source directory so that changes to the metadata in
#       the parent directories does not trigger a snapshot.
cd "${source:?Source not set}"

[ -d "${repo:?Repo not set}" ] || restic init --insecure-no-password --repo "$repo"
restic --insecure-no-password --repo "$repo" unlock

echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '${repo:?Repo not set.}'"
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
  --keep-weekly 12 \
  --keep-monthly 6 \
  --repo "$repo"

restic --insecure-no-password --repo "$repo" check
