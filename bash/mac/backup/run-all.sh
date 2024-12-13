#!/usr/bin/env bash

logFile="$HOME/logs/run-all-backups.log"
scriptPath="$(dirname -- "${BASH_SOURCE[0]}")"

{
    bash "$scriptPath/jetbrains-configs.sh"
    bash "$scriptPath/firefox.sh"
    bash "$scriptPath/mac-settings.sh"
    bash "$scriptPath/repos.sh"
    printf "\n\n"
} >> "$logFile" 2>&1
