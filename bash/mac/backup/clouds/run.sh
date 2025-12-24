#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. ./configs/clouds.sh

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
