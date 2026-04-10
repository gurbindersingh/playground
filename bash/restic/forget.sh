#!/usr/bin/env bash
set -e

config="${XDG_CONFIG_HOME:-$HOME/.config}/restic.sh"
[ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
. "$config"

restic forget --prune --keep-monthly 12 #--dry-run
echo ""
restic check
unset RESTIC_PASSWORD
