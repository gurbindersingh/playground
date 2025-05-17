#!/usr/bin/env bash
set -e

if [[ "$#" -lt 1 ]]; then
  echo "Missing PATH parameter"
  echo "Usage: restic-backup PATH..."
  exit 1
fi

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. ./configs/clouds.sh

backup_sources=("$@")

restic --insecure-no-password backup --skip-if-unchanged "${backup_sources[@]:?}"
restic --insecure-no-password check
