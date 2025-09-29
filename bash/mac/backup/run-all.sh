#!/usr/bin/env bash

logFile="$HOME/logs/run-all-backups.log"

{
  cd "$(dirname -- "${BASH_SOURCE[0]}")" || echo "[ERROR] Failed to cd." && exit 1
  bash jetbrains-configs.sh
  bash obsidian-configs.sh
  bash firefox.sh
  bash repos.sh
  printf "\n\n"
} >>"$logFile" 2>&1
