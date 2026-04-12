#!/usr/bin/env bash
set -e

if [[ $# -lt 1 ]]; then
  echo "ERROR: Missing arguments"
  echo "Usage: $0 SNAPSHOT"
  exit 1
fi

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
. "$config"

snapshot="$1"

restic --insecure-no-password ls "$snapshot"
