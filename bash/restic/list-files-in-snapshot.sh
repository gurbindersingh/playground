#!/usr/bin/env bash
set -e

if [[ $# -lt 1 ]]; then
    echo "ERROR: Missing arguments"
    echo "Usage: $(basename "$0") SNAPSHOT"
    exit 1
fi

config="${XDG_CONFIG_HOME:-$HOME/.config}/restic.sh"
[ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
. "$config"

snapshot="$1"

restic ls "$snapshot"
unset $RESTIC_PASSWORD
