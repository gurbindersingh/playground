#!/bin/bash

logFile="$HOME/logs/run-all-backups.log"
scriptPath="$(dirname -- "${BASH_SOURCE[0]}")"

{
  bash "$scriptPath/vscode-settings.sh"
  bash "$scriptPath/firefox.sh"
  bash "$scriptPath/mac-settings.sh"
  bash "$scriptPath/git-repos.sh"
  printf "\n\n"
} >> "$logFile" 2>&1
