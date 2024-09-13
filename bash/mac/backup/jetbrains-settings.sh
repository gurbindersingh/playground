#!/usr/bin/env bash
set -e

configs_dir="$HOME/Library/Application Support/JetBrains/"
# Load config variables 
. configs/jetbrains-dest.sh

for dest in "${targets[@]}"; do
    echo "[$(date +'%F %H:%M:%S')] Backing up $configs_dir to $dest"
    rsync -av "$configs_dir" "$dest"
done
