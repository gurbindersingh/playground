#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || {
  echo "Config not found: $config" >&2
  exit 1
}

. "$config"

# sources=()
# for cloud in "${clouds[@]:?}"; do
#   #   ./sync.sh "$HOME/$cloud/" "$main_drive/$cloud"
#   sources+=("$HOME/$cloud/")
# done

for drive in "${drives[@]:?}"; do
  if [[ -e "$drive" ]]; then
    export RESTIC_REPOSITORY="$drive/cloud_backups/"
    ./backup.sh "${clouds[@]:?}"
    ./forget-snapshots.sh
    ./list-snapshots.sh
  else
    echo "[INFO] Drive '$drive' is not connected"
    exit 0
  fi
done
