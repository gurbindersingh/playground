#!/usr/bin/env bash

# On macOS if you are having trouble with xargs splitting arguments at all 
# white spaces, do this.
tr '\n' '\0' < "file list.txt" | xargs -0 ls -lh
# On macOs xargs doesn't support the -d option for setting the delimiter, 
# and the -E option still splits arguments at any white space it encounters
# so we need to use this workaround in those cases.