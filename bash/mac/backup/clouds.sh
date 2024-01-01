#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

drive="/Volumes/Seagate"
readarray -t clouds < "clouds.txt"

if [[ ! -e $drive ]]; then
  echo "[ERROR] External drive $drive not found."
  exit 1
fi

for cloud in "${clouds[@]}"; do
  echo "[$(date +'%F %H:%M:%S')] Creating backup of '$cloud'"
  rsync -av \
    --exclude=".git" \
    --exclude=".tmp.drive*" \
    --exclude=".idea" \
    --exclude="target" \
    --exclude="*.ini" \
    --exclude="Sync.Cache" \
    "$HOME/$cloud" "${drive:?}"
    
  echo "[$(date +'%F %H:%M:%S')] DONE"
  echo ""
done
