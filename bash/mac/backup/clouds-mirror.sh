#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. configs/clouds.sh

drive="/Volumes/${mirror_drive:?}"
source_drive="/Volumes/${main_drive:?}"
timestamp="$(date +'%F_%H%M.%S')"

if [[ ! (-e "$drive" && -e "$source_drive") ]]; then
    echo "[ERROR] External drive $drive or $source_drive not found."
    exit 1
fi

for cloud in "${mirror_dirs[@]}"; do
    source="$source_drive/$cloud/"
    destination="$drive/$cloud/"

    # NOTE: Incremental backups do not work on some file systems, like exFAT.
    #       So instead we use the `--backup-dir` feature to create an archive 
    #       of deleted and changed files.
    echo "[$(date +'%F %H:%M:%S')] Creating backup of '$source' at '$destination'."
    rsync -avb \
        --backup-dir="$drive/$cloud.changed/$timestamp" \
        --delete-after \
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