#!/bin/bash

NOW="$(date +"%F_%H%M.%S")"
SRC="/apps/myapp"
BACKUP_DIR="/home/app/.backup/myapp"
PREVIOUS="${BACKUP_DIR}/previous"
OPTS="-av"
EXCLUDE=('**.git*' '**.md' '**/models/' '**/training/')

if [[ ! -e $SRC ]]; then
  printf "[INFO] --- The source directory '%s' does not exist. Skipping backup\n" "$SRC"
  exit 0
fi

if [[ -d $PREVIOUS ]]; then
  printf "[INFO] --- Renaming previous backup\n"
  mv -v "$PREVIOUS" "${BACKUP_DIR}${NOW}"
fi

printf "\n[INFO] --- Creating new directory '%s'\n" "$PREVIOUS"
mkdir -pv "$PREVIOUS"

for item in "${EXCLUDE[@]}"; do
  OPTS="$OPTS --exclude=$item"
done

printf "\n[INFO] --- Creating backup of '%s' at '%s'\n\n" "$SRC" "$PREVIOUS"
rsync $OPTS "$SRC" "$PREVIOUS"

LOGS_DIR="$PREVIOUS/logs"

if [[ -d $LOGS_DIR && $(find "$LOGS_DIR" -maxdepth 1 -iname "*.log" | wc -l) -gt 0 ]]; then
  OLD_LOGS_DIR="${LOGS_DIR}/old/"
  NOW=$(date +"%F_%H%M.%S")

  printf "\n[INFO] --- Moving old log files\n"
  # Append a timestamp to existing logs
  find "$LOGS_DIR" -maxdepth 1 -name "*.log" -exec mv -v "{}" "{}.$NOW" \;
  echo ""
  mkdir -pv "$OLD_LOGS_DIR"
  mv -v "${LOGS_DIR}"/*.log.* "$OLD_LOGS_DIR"
fi

printf "\n[INFO] --- Current backups:\n"
ls -1 "$BACKUP_DIR"

NUM_OF_BACKUPS=10
if [[ $(find "$BACKUP_DIR" -maxdepth 1 ! -iname "$BACKUP_DIR" ! -ipath "$BACKUP_DIR" | wc -l) -gt $NUM_OF_BACKUPS ]]; then
  printf "\n[INFO] --- There are more than %s backups. Only keeping the last %s.\n" "$NUM_OF_BACKUPS" "$NUM_OF_BACKUPS"
  # Since we already exclude the previous/ directory from the search, we only cut of NUM_OF_BACKUPS - 1 from the found list.
  find "$BACKUP_DIR" -maxdepth 1 ! -iname "prev*" ! -ipath "$BACKUP_DIR" | sort | head -n $((1 - NUM_OF_BACKUPS)) | xargs -d '\n' rm -rv

  printf "\n[INFO] --- Remaining backups:\n"
  ls -1 "$BACKUP_DIR"
fi
