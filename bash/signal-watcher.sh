#!/usr/bin/env bash
set -e

app_dir="$HOME/app"
log_file="$app_dir/signal-watcher.log"
stop_signal="signal.stop"
start_signal="signal.start"

{
  cd "$app_dir"
  if [[ -e $stop_signal ]]; then
    bash stop.sh
    rm -v $stop_signal
  elif [[ -e $start_signal ]]; then
    bash start.sh
    rm -v $start_signal
  fi
} >> "$log_file" 2>&1
