# Why the symlink is necessary

When we run a python script, only the parent directory of the script gets added to the `PYTHONPATH`. Because of that, any sibling directories cannot be resolved.
