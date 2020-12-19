#!/usr/bin/env bash

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory" || exit 1 # the exit command is not necessary if you use `set -e`

readarray -t array < file.txt
echo "${array[@]}"
