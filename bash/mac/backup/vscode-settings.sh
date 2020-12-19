#!/bin/bash
set -e

SRC="$HOME/Library/Application Support/Code"
USER_SETTINGS="$SRC/User"
DST="$HOME/Developer/dev-setup/vscode"

echo "[$(date +'%F %H:%M:%S')] Creating backup of VS Code settings"
rsync -av "$USER_SETTINGS/settings.json" "$USER_SETTINGS/snippets" "$DST"
rsync -av "$USER_SETTINGS/keybindings.json" "$DST/mac"
echo "[$(date +'%F %H:%M:%S')] DONE"
echo ""