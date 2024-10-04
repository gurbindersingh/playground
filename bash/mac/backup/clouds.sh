#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

drive="/Volumes/Seagate"
. configs/clouds.sh

if [[ ! -e $drive ]]; then
  echo "[ERROR] External drive $drive not found."
  exit 1
fi

for cloud in "${clouds[@]}"; do
  source="$HOME/$cloud/"
  destination="${drive:?}/$cloud/"
  echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '$destination'."
  rsync -avb \
    --exclude=".git" \
    --exclude=".tmp.drive*" \
    --exclude=".idea" \
    --exclude="target" \
    --exclude="*.ini" \
    --exclude="Sync.Cache" \
    "$source" "$destination"
    
  echo "[$(date +'%F %H:%M:%S')] DONE"
  echo ""
done
