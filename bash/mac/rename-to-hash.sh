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
  file_name="${hash_and_filename[1]}"

  IFS='.' read -ra name_and_extension <<< "$file_name"
  # name="${name_and_extension[0]}"
  extension="${name_and_extension[1]}"
  new_name="$hash.$extension"

  if [[ "$file_name" == "$new_name" ]]; then
    echo "Skipping $file_name"
    continue;
  fi

  # echo "$name.$extension -> $new_name"
  mv -v "$file" "$new_name"
done


