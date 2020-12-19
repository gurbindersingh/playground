#!/bin/bash

if [[ $# -lt 1 ]]; then
  echo "ERROR: missing SRC parameter"
  echo "Usage: compile.sh SRC [-r] [-c99]"
  echo "Flags:"
  echo "  -r    Run the program after compilation"
  echo "  -c99  Use the C99 standard"
  echo "  -omp  Use the OpenMP library"
  exit 1
fi

FILE=$1
OUT="out/${FILE::-2}"
RUN=""
VERSION=""
OPENMP=""

for i in "$@"; do
  if [[ $i == "-r" ]]; then
    RUN="./$OUT"
  elif [[ $i == "-c99" ]]; then
    VERSION="-std=c99"
  elif [[ $i == "-omp" ]]; then
    OPENMP="-fopenmp"  
  fi
done

echo "Output file at: $OUT"

gcc "$FILE" $VERSION $OPENMP -Wextra -Wall -Werror -fstack-protector -o "$OUT"
$RUN