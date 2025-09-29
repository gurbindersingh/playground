#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

. configs/jetbrains.sh

configs_dir="$HOME/Library/Application Support/JetBrains/"

for dest in "${targets[@]}"; do
  echo "[$(date +'%F %H:%M:%S')] Backing up $configs_dir to $dest"
  rsync -av --exclude='**.git' --exclude='**.jar' "$configs_dir" "$HOME/$dest"
done
