#!/bin/bash

logFile="$HOME/logs/run-all-backups.log"
scriptPath="$HOME/Developer/playground/bash/mac/backup"

{
  bash "$scriptPath/vscode-settings.sh"
  bash "$scriptPath/firefox.sh"
  bash "$scriptPath/mac-settings.sh"
  printf "\n\n"
} >> "$logFile" 2>&1
