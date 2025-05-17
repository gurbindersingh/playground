#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. configs/clouds.sh

drive="/Volumes/${mirror_drive:?}"
source_drive="/Volumes/${main_drive:?}"

if [[ ! (-e "$drive" && -e "$source_drive") ]]; then
    echo "[ERROR] External drive $drive or $source_drive not found."
    exit 1
fi

# restic --insecure-no-password init
cd "$source_drive"
restic --insecure-no-password backup --skip-if-unchanged ./
