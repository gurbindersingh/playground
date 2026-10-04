#!/usr/bin/env bash
set -e

if [[ $# -lt 1 ]]; then
  echo "ERROR: Missing arguments"
  echo "Usage: $(basename "$0") SNAPSHOT"
  exit 1
fi

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || {
  echo "Config not found: $config" >&2
  exit 1
}

. "$config"

snapshot="$1"

for drive in "${drives[@]:?}"; do
  if [[ -e "$drive" ]]; then
    export RESTIC_REPOSITORY="$drive/cloud_backups/"
    echo "[INFO] Listing current snapshots '$RESTIC_REPOSITORY'"
    restic ls "$snapshot"
  else
    echo "[INFO] Drive '$drive' is not connected"
    exit 0
  fi
done
