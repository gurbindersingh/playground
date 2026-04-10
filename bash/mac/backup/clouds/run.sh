#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
. "$config"

if [[ -e "${main_drive:?Variable not set}" ]]; then
  for cloud in "${clouds[@]}"; do
    ./sync.sh "$HOME/$cloud/" "$main_drive/$cloud"
  done
  # Remove the attribute files created by macOS
  dot_clean "$main_drive/"
else
  echo "[INFO] Drive '$main_drive' is not connected"
  exit 0
fi

if [[ ! -e "$mirror_drive" ]]; then
  echo "[INFO] Mirror drive not mounted. Not running restic backup."
  exit 0
fi

./restic-backup.sh "$main_drive"
./forget.sh
