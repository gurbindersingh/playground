#!/usr/bin/env bash
set -e

echo "[$(date +'%F %H:%M:%S')] Backing up Git repos"

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

dest="$(cat repos-dest.txt)"
readarray -t repos < "repos.txt"

for repo in "${repos[@]}"; do
  echo "[$(date +'%F %H:%M:%S')] Creating backup of '$repo'"
  rsync -av \
    --exclude=".git" \
    --exclude=".tmp.drive*" \
    --exclude=".idea" \
    --exclude="target" \
    --exclude="*.ini" \
    "$HOME/Developer/$repo" "$HOME/${dest:?}"
    
  echo ""
  echo "[$(date +'%F %H:%M:%S')] DONE"
  echo ""
done
echo "============================================================================="
echo ""

