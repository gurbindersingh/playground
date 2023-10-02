#!/bin/bash
set -e

if [[ $# -le 0 ]]; then
  echo "Missing FILE argument."
  echo "Usage: rename-to-hash.sh FILE..."
  exit 1
fi

files=( "$@" )
backup_location="$HOME/.renametohash.backups/"

printf "\n%s\n\n" "[INFO] Backing up files to ${backup_location}."
rsync -av "${files[@]}" "$backup_location"

for file in "${files[@]}"; do
  # The md5 command here is macOS specific
  hashed="$(md5 -r "$file")"
  
  IFS=' ' read -ra hash_and_filename <<< "$hashed"
  hash="${hash_and_filename[0]}"
  # echo "File: $file"
  # echo "Hash: $hash"

  IFS='.' read -ra name_and_extension <<< "$file"
  extension="${name_and_extension[1]}"
  old_name=$(basename "$file")
  new_name="${file/${old_name}/${hash}.${extension}}"
  # echo "Basename: $old_name"
  # echo "Renaming $file -> $new_name"

  if [[ "$file" == "$new_name" ]]; then
    echo "File '$file' is already hashed. Skipping."
    continue;
  fi

  mv -v "$file" "$new_name"
  echo ""
done


