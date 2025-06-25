#!/usr/bin/env bash
set -e

if [[ $# -le 0 ]]; then
  echo "Missing FILE argument."
  echo "Usage: rename-to-hash.sh FILE..."
  exit 1
fi

files=("$@")
backup_location="$HOME/.renametohash.backups/"

for file in "${files[@]}"; do
  echo ""
  # Hash the file and extract the hash from the returned string.
  # The md5 command here is macOS specific
  hash="$(md5 -r "$file" | awk '{print $1}')"

  # Split on every dot and get the last string in the list.
  extension="$(awk -F '.' '{print $NF}' <<<"$file")"
  old_name=$(basename "$file")
  # Use bash parameter expansion to replace the old name in the file path with
  # the new name.
  new_name="${file/"${old_name}"/"${hash}.${extension}"}"
  # echo "Basename: $old_name"

  if [[ "$file" == "$new_name" ]]; then
    echo "File '$file' is already hashed. Skipping."
    continue
  fi

  if [[ -e "$new_name" ]]; then
    echo "File $new_name already exists. Skipping."
    continue
  fi

  printf "%s\n" "[INFO] Backing up files to '${backup_location}'."
  rsync -a "$file" "$backup_location"

  # echo "Renaming $file -> $new_name"
  mv -v "$file" "$new_name"
done
