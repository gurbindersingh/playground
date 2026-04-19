#!/usr/bin/env bash
set -e

if [[ "$#" -lt 1 ]]; then
  echo "Missing PATH parameter"
  echo "Usage: $(basename "$0") PATH..."
  exit 1
fi

backup_sources=("$@")

if [[ ! -e "${RESTIC_REPOSITORY:?}" ]]; then
  read -rp "Repository '$RESTIC_REPOSITORY' not found. Initialize now? (y/n) " confirm

  if [[ "$confirm" == "y" ]]; then
    echo "[INFO] Initializing repository '$RESTIC_REPOSITORY'."
    restic init
  fi
fi

if [[ ! -e "${RESTIC_REPOSITORY:?}" ]]; then
  echo "[ERROR] Repository not found. Not running backup." >&2
  exit 1
fi

echo "[INFO] Creating backups of ${backup_sources[*]} at $RESTIC_REPOSITORY"
restic backup \
  --skip-if-unchanged \
  --exclude-file "${exclude_file:?}" \
  "${backup_sources[@]:?}"
# --dry-run \
restic check
