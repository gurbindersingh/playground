#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

time="$(date +'%T')"
theme="dark"
threshold="16:30:00"

if [[ "$time" < "$threshold" ]]; then
  theme="light"
fi
# echo "$theme"

currentWallpapers="$HOME/themed_wallpapers"
allWallpapers="$HOME/$(cat wallpaper-location.txt)"
currentTheme="$currentWallpapers/$theme"
logFile="$HOME/logs/set-wallpapers.log"

{
  echo "" 
  if [[ -e "$currentTheme" ]]; then
    echo "[$(date +'%F %H:%M:%S')] Nothing to do." 
    exit 0
  fi
  echo "[$(date +'%F %H:%M:%S')] Setting wallpapers for $theme theme." 

  rm -r "${currentWallpapers:?}/"
  mkdir -p "$currentWallpapers"
  ln "$allWallpapers/$theme"/* "$currentWallpapers"
  touch "$currentWallpapers/$theme"

  echo "[$(date +'%F %H:%M:%S')] Done." 
} >> "$logFile" 2>&1
