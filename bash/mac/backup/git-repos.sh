#!/usr/bin/env bash
set -e

echo "[$(date +'%F %H:%M:%S')] Backing up Git repos"

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

dest="$(cat configs/repos-dest.txt)"
# The preferred method for reading lines into an array should be `readarray` 
# but on macOS if we run a script using launchd instead of cron the deprecated 
# version of Bash (3.x) is used. This is a workaround for the older version.
# The `-n` option of the test command checks if the string is non-zero.
while IFS= read -r line || [ -n "$line" ]; do
  repos+=("$line")
done < "configs/repos.txt"

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

