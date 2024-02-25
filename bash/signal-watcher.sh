#!/usr/bin/env bash
set -e

app_dir="$HOME/app"
log_file="$app_dir/signal-watcher.log"
stop_signal="signal.stop"
start_signal="signal.start"
restart_signal="signal.restart"

{
  cd "$app_dir"
  if [[ -e $stop_signal ]]; then
    bash stop.sh
    rm -v $stop_signal
  elif [[ -e $start_signal ]]; then
    bash start.sh
    rm -v $start_signal
  elif [[ -e $restart_signal ]]; then
    bash stop.sh
    bash start.sh
    rm -v $restart_signal
  fi
} >> "$log_file" 2>&1
