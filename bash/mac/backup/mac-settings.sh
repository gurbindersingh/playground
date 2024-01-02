#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

dest="$HOME/$(cat mac.txt)"

echo "[$(date +'%F %H:%M:%S')] Backing up Mac settings"
defaults read > "$dest/defaults.txt"
defaults read -g > "$dest/defaults.global.txt"
echo "[$(date +'%F %H:%M:%S')] DONE"
echo "============================================================================="
echo ""
