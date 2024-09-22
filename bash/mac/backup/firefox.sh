#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

source="$HOME/Library/Application Support/Firefox/Profiles"
. configs/ff-settings.sh

echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '$dest'"
rsync -a "$source" "$HOME/$dest"
echo "[$(date +'%F %H:%M:%S')] DONE"
echo "============================================================================="
echo ""
