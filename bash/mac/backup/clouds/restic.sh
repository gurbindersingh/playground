#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. ./configs/clouds.sh

# If the drive is not mounted, exit.
if [[ ! -e "${main_drive:?Variable not found.}" ]]; then
  echo "[ERROR] External drive $main_drive not found."
  exit 1
fi

restic --insecure-no-password backup --skip-if-unchanged "${clouds[@]:?Variable not found.}"
restic --insecure-no-password check

# If the drive is not mounted, exit.
if [[ ! -e "${mirror_drive:?Variable not found.}" ]]; then
  echo "[INFO] External drive $mirror_drive not found. Skipping syncing."
  exit 0
fi

rsync -av --delete-after "$RESTIC_REPOSITORY" "$mirror_drive/"

export RESTIC_REPOSITORY="$mirror_drive/clouds.backup"
restic --insecure-no-password check
# restic --insecure-no-password forget --prune --keep-monthly 12 --dry-run
# restic --insecure-no-password check
