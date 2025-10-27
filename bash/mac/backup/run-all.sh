#!/usr/bin/env bash
set -e
logFile="$HOME/logs/run-all-backups.log"

{
  echo "[DEBUG] Changing into script's directory."
  cd "$(dirname -- "${BASH_SOURCE[0]}")" || {
    echo "[ERROR] Failed to cd."
    exit 1
  }
  set +e
  echo "[INFO] Running backups"
  bash jetbrains-configs.sh
  bash firefox.sh
  bash repos.sh
  printf "\n\n"
} >>"$logFile" 2>&1
