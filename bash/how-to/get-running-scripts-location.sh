#!/usr/bin/env bash

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script

# This works as long as the script is not called using a symlink. Otherwise
# use the solution below
directory="$(dirname -- "${BASH_SOURCE[0]}")"
echo "$directory"

# SOURCE=${BASH_SOURCE[0]}
# while [ -L "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
#   DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
#   SOURCE=$(readlink "$SOURCE")
#   [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
# done
# DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
