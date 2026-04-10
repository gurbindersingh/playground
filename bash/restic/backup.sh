#!/usr/bin/env bash
set -e

config="${XDG_CONFIG_HOME:-$HOME/.config}/restic.sh"
[ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
. "$config"

restic backup ./
bash .forget.sh
unset RESTIC_PASSWORD
