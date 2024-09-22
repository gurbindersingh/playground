#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. configs/mac.sh

echo "[$(date +'%F %H:%M:%S')] Backing up Mac settings"
defaults read > "$HOME/$cloud/defaults.txt"
defaults read -g > "$HOME/$cloud/defaults.global.txt"

echo "[$(date +'%F %H:%M:%S')] DONE"
echo "============================================================================="
echo ""
