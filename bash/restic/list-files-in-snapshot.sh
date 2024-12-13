#!/usr/bin/env bash
set -e

if [[ $# -lt 1 ]]; then
    echo "ERROR: Missing arguments"
    echo "Usage: list-files-in-snapshot.sh SNAPSHOT"
    exit 1
fi

. .config.sh

snapshot="$1"

restic ls "$snapshot"
unset $RESTIC_PASSWORD
