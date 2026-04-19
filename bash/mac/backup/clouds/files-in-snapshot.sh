#!/usr/bin/env bash
set -e

if [[ $# -lt 1 ]]; then
  echo "ERROR: Missing arguments"
  echo "Usage: $(basename "$0") SNAPSHOT"
  exit 1
fi

snapshot="$1"

restic ls "$snapshot"
