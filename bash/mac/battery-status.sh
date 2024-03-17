#!/usr/bin/env bash
set -e

logFile="$HOME/logs/battery-status.log"
status="$(pmset -g ps | grep -Eo '[0-9]{1,3}%; (dis)?charg(ing|ed)')"
state="$(echo "$status" | grep -Eo '[0-9]{1,3}%; (dis)?charg(ing|ed)')"
percentage="$(echo "$status" | grep -Eo '[0-9]{1,3}')"

echo "[$(date +'%F %H:%M:%S')] Battery at $status." >> "$logFile" 2>&1
if [[ $state == 'discharging' && $percentage -lt 30 || $state == 'charging' && $percentage -gt 75 ]]; then
  osascript -e 'display notification "'"Battery at $status."'" with title "Battery status"'
fi
