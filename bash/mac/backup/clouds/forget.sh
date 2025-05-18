#!/usr/bin/env bash
set -e

. ./configs/clouds.sh

restic --insecure-no-password forget \
  --prune \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 12 \
  --keep-yearly 3 #--dry-run
echo ""
restic --insecure-no-password check
