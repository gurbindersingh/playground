#!/usr/bin/env bash
set -e

. configs/obsidian.sh

for vault in "${vaults[@]?:Not set}"; do
  echo "[$(date +'%F %H:%M:%S')] Creating backup of '$vault/.obsidian/'."
  rsync -avub \
    --exclude=".DS_Store" \
    --exclude="/workspace.json" \
    --exclude="**/plugins/**/main.js" \
    --exclude="**/plugins/**/manifest.json" \
    --exclude="**/plugins/**/styles.css" \
    "$HOME/$vault/.obsidian/" "$HOME/${dest:?Not set}"

  echo ""
  echo "[$(date +'%F %H:%M:%S')] DONE"
  echo ""
done
echo "============================================================================="
echo ""
