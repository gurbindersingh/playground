#!/usr/bin/env bash
set -e

echo "[$(date +'%F %H:%M:%S')] Backing up Git repos"

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

. ./configs/repos.sh

echo "[$(date +'%F %H:%M:%S')] Creating backup of '$repos'"
rsync -av \
  --exclude=".tmp.drive*" \
  --exclude=".idea" \
  --exclude="target" \
  --exclude="*.ini" \
  --exclude="node_modules" \
  --exclude=".venv" \
  "$HOME/${repos:?}" "$HOME/${dest:?}"

echo ""
echo "[$(date +'%F %H:%M:%S')] DONE"
echo ""
echo "============================================================================="
echo ""
