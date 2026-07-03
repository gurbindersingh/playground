#!/usr/bin/env bash
set -e

if [[ $# -le 0 ]]; then
  echo "Missing FILE argument."
  echo "Usage: $(basename "$0") FILE..."
  exit 1
fi

files=("$@")
backup_location="$HOME/.renametohash.backups/"

for file in "${files[@]}"; do
  echo ""

  if file "$file" | grep -ivq 'image'; then
    echo "[WARN] File '$file' is not an image. Skipping."
    continue
  fi
  # Hash the file and extract the hash from the returned string.
  hash="$(image-hashing "$file" | awk '{print $1}')"

  # Split on every dot and get the last string in the list.
  # extension="$(awk -F '.' '{print $NF}' <<<"$file")"
  extension="${file##*.}"
  old_name=$(basename "$file")
  # Use bash parameter expansion to replace the old name in the file path with
  # the new name.
  #new_name="${file/"${old_name}"/"${hash}.${extension}"}"
  new_name="${file/"${old_name}"/"${hash}"}"
  # echo "Basename: $old_name"

  if [[ "$file" == "$new_name.$extension" ]]; then
    echo "[WARN] File '$file' is already hashed. Skipping."
    continue
  fi

  if [[ -e "$new_name.$extension" ]]; then
    new_name="$new_name.$(date +'%F_%H%M%S')"
  fi

  printf "%s\n" "[INFO] Backing up files to '${backup_location}'."
  rsync -a "$file" "$backup_location"

  # echo "Renaming $file -> $new_name"
  mv -vn "$file" "$new_name.$extension"
done
