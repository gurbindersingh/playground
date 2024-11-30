#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. configs/firefox.sh

source="$HOME/Library/Application Support/Firefox/Profiles"
now="$(date +'%F.%H%M.%S')"

echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '$dest'"
rsync -av --delete-after --backup-dir="$now" "$source" "$HOME/$dest"
echo "[$(date +'%F %H:%M:%S')] DONE"
echo "============================================================================="
echo ""
