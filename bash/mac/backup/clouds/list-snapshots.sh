#!/usr/bin/env bash
set -e

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || {
  echo "Config not found: $config" >&2
  exit 1
}

. "$config"

for drive in "${drives[@]:?}"; do
  if [[ -e "$drive" ]]; then
    export RESTIC_REPOSITORY="$drive/cloud_backups/"
    echo "[INFO] Listing current snapshots '$RESTIC_REPOSITORY'"
    restic snapshots
  else
    echo "[INFO] Drive '$drive' is not connected"
    exit 0
  fi
done
