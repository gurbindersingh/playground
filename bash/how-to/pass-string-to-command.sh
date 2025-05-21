#!/usr/bin/env bash

str=$"Some string.
Some number.
"

grep 'st' <<<"$str"
