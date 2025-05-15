#!/usr/bin/env bash
set -e

. .config.sh

restic forget --prune --keep-monthly 12 #--dry-run
echo ""
restic check
unset RESTIC_PASSWORD
