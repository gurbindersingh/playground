#!/bin/bash

BACKUP_DIR="/home/app/.backup/myapp"
APP_DIR="/apps/myapp"
PREVIOUS_BACKUP="${BACKUP_DIR}/previous"
LOGS="$APP_DIR/logs"

if [[ -d $LOGS ]]; then
  printf "[INFO] --- Backing up current logs for debugging\n"
  rsync -av "$LOGS/" "${PREVIOUS_BACKUP}/logs/"
fi

printf "[INFO] --- Saving PID of running process\n"
rsync -av "$APP_DIR/myapp.pid" "${PREVIOUS_BACKUP}/"

printf "\n[INFO] --- Deleting current version\n"
rm -rv "${APP_DIR:?}/"*

printf "\n[INFO] --- Restoring previous version\n"
mv -v "$PREVIOUS_BACKUP"/* "$APP_DIR/"
rm -rv "$PREVIOUS_BACKUP"

if [[ $(ls -1 "$BACKUP_DIR" | wc -l) -gt 0 ]]; then
  LATEST="$BACKUP_DIR/$(ls -1tr -I *.old "$BACKUP_DIR" | head -n 1)"
  printf "\n[INFO] --- Renaming '%s' to '%s'\n" "$LATEST" "$PREVIOUS_BACKUP"
  mv -v "$LATEST" "$PREVIOUS_BACKUP"
fi
