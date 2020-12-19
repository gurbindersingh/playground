#!/bin/bash

# TODO: Add options to list and clear trash using getopts

if [[ $# -lt 1 ]]; then
  echo "Missing parameter"
  echo "Usage: trash.sh [OPTIONS] FILE..."
  exit 1
fi

trashcan="$HOME/.trash-can/"
mv -v "$@" "$trashcan"
