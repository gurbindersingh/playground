#!/usr/bin/env bash
set -e

echo "[INFO] Pruning old backups."
restic forget \
  --prune \
  --keep-weekly 26 \
  --keep-monthly 12 \
  --keep-yearly 5
echo ""
restic check
