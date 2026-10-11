# Refactor backups

- Use a single script for every backup
- Use JSON for the config file (source, repo, retention, any specific restic parameters)
- Use `jq` to read the JSON
- Store encryption password using `pass`, instead of in plaintext
- Only issue is how to run the other restic commands on specific sources, e.g.
  listing all snapshots for specific source
