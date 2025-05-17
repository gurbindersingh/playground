#!/usr/bin/env bash
set -e

if [[ $# -lt 1 ]]; then
  echo "ERROR: Missing arguments"
  echo "Usage: list-files-in-snapshot.sh SNAPSHOT"
  exit 1
fi

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. ./configs/clouds.sh

snapshot="$1"

restic --insecure-no-password ls "$snapshot"
