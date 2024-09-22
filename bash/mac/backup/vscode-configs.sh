#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1

SRC="$HOME/Library/Application Support/Code"
USER_SETTINGS="$SRC/User"

. configs/vscode-dest.sh

echo "[$(date +'%F %H:%M:%S')] Creating backup of VS Code settings at '$DST'"
rsync -av "$USER_SETTINGS/settings.json" "$USER_SETTINGS/snippets" "$DST"
cp -v "$USER_SETTINGS/keybindings.json" "$DST/mac.keybindings.json"
echo "[$(date +'%F %H:%M:%S')] Making copy to '$COPY_AT'"
rsync -av "$DST/" "$COPY_AT/"
echo "[$(date +'%F %H:%M:%S')] DONE"
echo "============================================================================="
echo ""
