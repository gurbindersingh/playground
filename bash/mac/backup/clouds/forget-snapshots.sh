#!/usr/bin/env bash
set -e

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || {
  echo "Config not found: $config" >&2
  exit 1
}

. "$config"

echo "[INFO] Pruning old backups."
restic forget \
  --prune \
  --keep-weekly 26 \
  --keep-monthly 12 \
  --keep-yearly 5
echo ""
restic check
