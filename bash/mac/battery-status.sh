#!/usr/bin/env bash
set -e

logFile="$HOME/logs/battery-status.log"
# echo "here"
status="$(pmset -g ps | grep -Eo '[0-9]{1,3}%; (dis)?charg(ing|ed)')"
state="$(echo "$status" | grep -Eo '(dis)?charg(ing|ed)')"
percentage="$(echo "$status" | grep -Eo '[0-9]{1,3}')"
message="Battery at ${percentage}%. ${state^}"

# echo "here"
if [[ $state == 'discharging' && $percentage -lt 30 || $state == 'charging' && $percentage -gt 70 ]]; then
  osascript -e 'display notification "'"$message"'" with title "Battery status"'
fi
echo "[$(date +'%F %H:%M:%S')] $message." >> "$logFile" 2>&1
