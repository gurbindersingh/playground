# Learn jq

`jq` is a command-line JSON processor. It reads JSON values, runs a filter for
each input value, and writes JSON values. Think of a filter as a small program:
`.` is its current input, and `|` passes output to the next filter.

Examples assume jq 1.6 or later and a POSIX-like shell such as Bash or Zsh.

## Start Here

```bash
# Install jq on macOS.
brew install jq

# Validate and pretty-print JSON. `.` is the identity filter.
printf '%s\n' '{"name":"Ada","active":true}' | jq '.'

# Read JSON from a file.
jq '.' config.json

# Compact JSON onto one line per output value.
jq -c '.' config.json

# Exit non-zero when the filter result is `false` or `null`.
jq -e '.healthy == true' status.json >/dev/null
```

Use single quotes around filters so the shell does not expand `$variables`,
backslashes, glob characters, or command substitutions before jq sees them.

## Input And Output

```bash
# jq reads a stream of JSON values, not necessarily one JSON value per file.
printf '%s\n' '1' '2' '{"three":3}' | jq '.'

# `-n` supplies `null` as input and does not read standard input.
jq -n '{name: "Ada", languages: ["jq", "shell"]}'

# `-s` (slurp) reads all input JSON values into one array.
printf '%s\n' '{"id":1}' '{"id":2}' | jq -s '.'
# => [{"id":1},{"id":2}]

# `-R` reads each input line as a raw string, rather than JSON.
printf '%s\n' alpha beta | jq -R '.'

# `-Rs` reads all raw input as one string.
printf 'alpha\nbeta\n' | jq -Rs '.'

# `-r` writes strings without JSON quotes. Use it for text, not JSON documents.
printf '%s\n' '{"name":"Ada"}' | jq -r '.name'
# => Ada

# `-j` is like `-r`, but does not append a newline.
printf '%s\n' '"token"' | jq -jr '.'
```

## Values, Pipes, And Multiple Results

```bash
# JSON literals are jq filters.
jq -n 'null, true, false, 42, "text", [1, 2], {name: "Ada"}'

# `|` gives each left-side output to the right-side filter.
jq -n '1 | . + 2 | . * 3'
# => 9

# `,` emits each expression as a separate output.
jq -n '"first", "second"'

# A filter can emit multiple outputs. `[]` iterates an array.
printf '%s\n' '[10,20,30]' | jq '.[]'

# Brackets collect all outputs into an array.
printf '%s\n' '[1,2,3]' | jq '[.[] | . * 10]'
# => [10,20,30]

# Parentheses control filter grouping.
jq -n '[(1, 2, 3) | . * 2]'
# => [2,4,6]
```

This multiple-output behavior is jq's most important non-obvious feature. For
example, `.users[] | .name` produces one output per user, while `[.users[] |
.name]` produces one array of names.

## Read Objects And Arrays

```bash
data='{
  "user": {"name":"Ada", "email":null},
  "tags": ["jq", "shell"],
  "keys with spaces": true
}'

# Object fields.
printf '%s\n' "$data" | jq '.user.name'
printf '%s\n' "$data" | jq '.["user"]["name"]'

# Quote keys that are not jq identifiers.
printf '%s\n' "$data" | jq '."keys with spaces"'

# Array indices, including a negative index from the end.
printf '%s\n' "$data" | jq '.tags[0], .tags[-1]'

# Slices: the end is exclusive. Omit either bound when needed.
printf '%s\n' "$data" | jq '.tags[0:1], .tags[1:]'

# Missing object keys and out-of-range array positions normally produce null.
printf '%s\n' "$data" | jq '.user.missing, .tags[99]'

# Provide a fallback for `null` or `false`.
printf '%s\n' "$data" | jq '.user.email // "not configured"'

# `?` suppresses type errors and emits `empty` instead.
printf '%s\n' '42' | jq '.name?'
```

## Build JSON

```bash
# Construct an object and an array.
printf '%s\n' '{"first":"Ada","last":"Lovelace"}' |
  jq '{name: "\(.first) \(.last)", roles: ["author", "programmer"]}'

# Shorthand copies fields from the current input.
printf '%s\n' '{"name":"Ada","id":7,"secret":"x"}' |
  jq '{id, name}'

# Dynamic key expressions need parentheses.
printf '%s\n' '{"name":"Ada","score":9}' |
  jq '{(.name): .score}'

# String interpolation uses `\(...)` inside a jq string.
printf '%s\n' '{"name":"Ada","score":9}' |
  jq '"\(.name) scored \(.score)"'

# Concatenate arrays; merge objects shallowly (right side wins).
jq -n '[1, 2] + [3]'
jq -n '{a: 1, nested: {left: true}} + {b: 2, nested: {right: true}}'

# `*` recursively merges objects.
jq -n '{nested: {left: true}} * {nested: {right: true}}'
```

## Select, Map, Sort, And Group

```bash
users='[
  {"id":"a1","name":"Ada","team":"core","active":true,"score":8},
  {"id":"b2","name":"Ben","team":"docs","active":false,"score":5},
  {"id":"c3","name":"Cy","team":"core","active":true,"score":10}
]'

# `select` retains inputs for which its condition is true.
printf '%s\n' "$users" | jq '.[] | select(.active)'

# Build an array of selected values.
printf '%s\n' "$users" | jq '[.[] | select(.team == "core") | .name]'

# `map(filter)` transforms every array element and returns an array.
printf '%s\n' "$users" | jq 'map({id, name, score: (.score * 10)})'

# `map_values` transforms values in an object.
jq -n '{a: 1, b: 2} | map_values(. * 10)'

# Sort objects by a field. `sort_by` sorts ascending.
printf '%s\n' "$users" | jq 'sort_by(.score) | reverse'

# `unique_by` deduplicates by a key; it sorts as part of the operation.
printf '%s\n' "$users" | jq 'unique_by(.team)'

# `group_by` requires values to be sorted by its key first.
printf '%s\n' "$users" | jq 'sort_by(.team) | group_by(.team)'

# Count, test whether any/all match, and get the first matching object.
printf '%s\n' "$users" | jq 'length, any(.[]; .active), all(.[]; .score >= 5)'
printf '%s\n' "$users" | jq 'first(.[] | select(.id == "c3"))'
```

## Update And Delete

Every jq update produces a new JSON value. jq never modifies its input file by
itself.

```bash
# Set a field. Missing intermediate object fields are created as needed.
printf '%s\n' '{"service":{"port":8080}}' |
  jq '.service.port = 9090 | .service.enabled = true'

# Update based on the existing value.
printf '%s\n' '{"retries":2,"tags":["stable"]}' |
  jq '.retries += 1 | .tags += ["fast"]'

# Delete an object field or array element.
printf '%s\n' '{"public":1,"secret":2,"items":["a","b","c"]}' |
  jq 'del(.secret, .items[1])'

# Update every matching object in an array, without relying on its index.
printf '%s\n' "$users" |
  jq 'map(if .id == "b2" then .active = true | .team = "core" else . end)'

# Update a nested array similarly.
printf '%s\n' '{"users":[{"id":"a1","role":"reader"},{"id":"b2","role":"reader"}]}' |
  jq '.users |= map(if .id == "b2" then .role = "admin" else . end)'

# Delete matching objects rather than mutate them.
printf '%s\n' "$users" | jq 'map(select(.active))'

# Use `with_entries` to transform object keys or values.
jq -n '{first_name: "Ada", last_name: "Lovelace"} |
  with_entries(.key |= gsub("_"; "-"))'
```

## Safe Bash Variables And File Updates

```bash
target_id='b2'
new_team='platform'
new_port=9090

# `--arg` passes a shell value as a JSON string. Never splice it into a filter.
printf '%s\n' "$users" |
  jq --arg id "$target_id" --arg team "$new_team" '
    map(if .id == $id then .team = $team else . end)
  '

# `--argjson` passes a shell value parsed as JSON (number, boolean, array, etc.).
printf '%s\n' '{"service":{}}' |
  jq --argjson port "$new_port" '.service.port = $port'

# `--slurpfile` reads JSON values from a file into an array variable.
jq --slurpfile defaults defaults.json '. * $defaults[0]' config.json

# Safely replace a file only after jq succeeds. `mktemp` keeps the temporary
# file in the same directory, so `mv` is atomic on the same filesystem.
file='users.json'
tmp=$(mktemp "${file}.tmp.XXXXXX") || exit 1
jq --arg id "$target_id" --arg team "$new_team" '
  map(if .id == $id then .team = $team else . end)
' "$file" >"$tmp" && mv "$tmp" "$file"

# Preserve the original file if jq fails. Remove the temporary file on exit.
tmp=$(mktemp "${file}.tmp.XXXXXX") || exit 1
trap 'rm -f "$tmp"' EXIT
jq --arg id "$target_id" --arg team "$new_team" '
  map(if .id == $id then .team = $team else . end)
' "$file" >"$tmp" && mv "$tmp" "$file"
```

If exactly one match is required, validate that assumption before updating:

```bash
jq -e --arg id "$target_id" '[.[] | select(.id == $id)] | length == 1' "$file" \
  >/dev/null || { printf 'expected exactly one user with id %s\n' "$target_id" >&2; exit 1; }
```

## Convert Object Entries

```bash
# Object -> [{key, value}, ...]. Useful when filtering or transforming keys.
jq -n '{ada: 8, ben: 5} | to_entries'

# [{key, value}, ...] -> object.
jq -n '[{key: "ada", value: 8}, {key: "ben", value: 5}] | from_entries'

# Filter object fields by their values.
jq -n '{ada: 8, ben: 5, cy: 10} |
  with_entries(select(.value >= 8))'
```

## Aggregate Data

```bash
# `add` reduces numbers, strings, arrays, or objects using `+`.
jq -n '[1, 2, 3] | add'
jq -n '[["a"], ["b"], ["c"]] | add'

# `reduce` gives explicit control over an accumulator.
jq -n 'reduce range(1; 6) as $n (0; . + $n)'
# => 15

# Produce a lookup object from an array.
printf '%s\n' "$users" |
  jq 'reduce .[] as $user ({}; .[$user.id] = $user.name)'

# Count items by a computed key.
printf '%s\n' "$users" |
  jq 'reduce .[] as $user ({}; .[$user.team] = ((.[$user.team] // 0) + 1))'
```

## Variables, Functions, Paths, And Recursion

```bash
# `as` binds an immutable jq variable while preserving the pipeline input.
# Capture a user before iterating the full saved input to count its teammates.
printf '%s\n' "$users" |
  jq '. as $all | $all[] as $user |
      {name: $user.name, team_size: [$all[] | select(.team == $user.team)] | length}'

# Define reusable filters. Function arguments are separated with semicolons.
jq -n '
  def clamp($min; $max): if . < $min then $min elif . > $max then $max else . end;
  120 | clamp(0; 100)
'

# `paths` emits paths; `getpath`, `setpath`, and `delpaths` work with them.
jq -n '{service: {port: 8080}, features: ["a", "b"]} | paths(scalars)'
jq -n '{service: {port: 8080}} | getpath(["service", "port"])'
jq -n '{} | setpath(["service", "port"]; 8080)'

# Recursively visit values. `..` includes the starting input itself.
printf '%s\n' '{"a":1,"nested":{"b":2,"items":[3]}}' |
  jq '.. | numbers'

# Recursively replace every string value.
printf '%s\n' '{"name":"Ada","nested":["jq",3]}' |
  jq '(.. | strings) |= ascii_upcase'
```

## Common Utilities

```bash
# Type and predicates.
jq -n '42 | type, isnormal, isfinite'
jq -n '"Ada" | length, ascii_downcase, startswith("A"), test("^A")'

# String conversion and regular expressions.
jq -n '"  42  " | ltrimstr("  ") | rtrimstr("  ") | tonumber'
jq -n '"first_name" | gsub("_"; "-")'
jq -n '"Ada Lovelace" | split(" ") | join("-")'

# Dates use seconds since the Unix epoch in jq's built-ins.
jq -n 'now | todateiso8601'
jq -n '"2026-07-20T12:00:00Z" | fromdateiso8601'

# Encode values for transport in URLs, CSV, JSON strings, or base64.
jq -n -r '"a value & more" | @uri'
jq -n -r '["Ada", "Lovelace"] | @csv'
jq -n -r '"secret" | @base64'
```

## Gotchas

- **`//` means “not `null` and not `false`,” not merely “missing.”** Use `if has("enabled") then .enabled else true end` when `false` is a meaningful configured value.
- **`empty` emits no value; `null` emits one value.** `select(false)` and `.field?` on an incompatible type can silently remove an item from a pipeline. Wrap outputs in `[...]` when you need to inspect cardinality.
- **A filter can produce many results.** `.items[] | .name` writes multiple JSON strings. Use `first(...)`, `last(...)`, `[ ... ]`, or `only(...)` when one result is required.
- **`map(if .id == $id then ... end)` updates every duplicate ID.** Validate uniqueness before a targeted update if duplicates would be a data error.
- **`--arg` creates a string.** `--arg count 3` makes `$count == "3"`; use `--argjson count 3` for the JSON number `3`. Do not use `--argjson` with untrusted text unless it is expected to be valid JSON.
- **Never interpolate shell data into the jq program.** Prefer `jq --arg value "$value" '.name = $value'` over building a quoted filter string. It avoids shell quoting bugs and jq injection.
- **`-r` is for text output.** `jq -r '.'` can create output that is not valid JSON when the result is a string. Omit `-r` when writing a JSON file.
- **jq does not have a portable safe `--in-place` mode.** Redirecting to the same file truncates it before jq reads it. Write to `mktemp`, then `mv` only on success.
- **`+` and `*` merge objects differently.** `+` replaces a whole colliding nested value; `*` recursively merges objects. Neither automatically gives a universally correct array-merge policy.
- **`group_by` needs sorted input.** Always write `sort_by(.key) | group_by(.key)` unless the input is already guaranteed sorted.
- **Object key order is not JSON semantics.** jq commonly preserves or sorts keys depending on the operation, but consumers must not depend on object member order. Use `-S` when deterministic sorted keys are useful for diffs.
- **JSON has only IEEE-754 numbers.** Very large integers can lose precision. Keep identifiers such as account IDs as JSON strings.
- **Shell `echo` is not reliable for arbitrary data.** Prefer `printf '%s\n' "$json"` so leading dashes and backslashes are not interpreted.
- **Avoid `eval` on jq output.** Even `@sh` output should generally be passed as arguments or handled by a dedicated parser rather than executed as shell code.

## Discover More

```bash
# Built-in help and the full manual.
jq --help
man jq

# Compile a filter without processing input.
jq -n 'def active: select(.active); 1'

# Use a filter file for non-trivial programs.
jq -f report.jq users.json
```

Official manual: <https://jqlang.org/manual/>
