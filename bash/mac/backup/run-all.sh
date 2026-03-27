#!/usr/bin/env bash
set -e
today="$(date +'%F')"
log_file="$HOME/logs/run-all-backups.$today.log"

{
  echo "[DEBUG] Changing into script's directory."
  cd "$(dirname -- "${BASH_SOURCE[0]}")" || {
    echo "[ERROR] Failed to cd."
    exit 1
  }
  set +e
  echo "[INFO] Running backups"
  bash firefox.sh
  bash thunderbird.sh
  bash repos.sh
  printf "\n\n"
} >>"$log_file" 2>&1
