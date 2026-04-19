#!/usr/bin/env bash
set -e

if [[ "$#" -lt 1 ]]; then
  echo "Missing PATH parameter"
  echo "Usage: $(basename "$0") PATH..."
  exit 1
fi

backup_sources=("$@")

restic \
  --insecure-no-password backup \
  --skip-if-unchanged \
  --exclude-file "$HOME/.configs/restic-exclude-cloud" \
  "${backup_sources[@]:?}"
# --dry-run \
restic --insecure-no-password check
