#!/usr/bin/env bash
set -e

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || { echo "Config not found: $config" >&2; exit 1; }
. "$config"

restic --insecure-no-password forget \
  --prune \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 12 \
  --keep-yearly 3 #--dry-run
echo ""
restic --insecure-no-password check
