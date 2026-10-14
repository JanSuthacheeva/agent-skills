I finished the merge as commit `5be19f3` on `main`, keeping git's default message:

```
Merge branch 'feature/invoice-currency'

# Conflicts:
#	api/invoices.py
```

Before committing I checked that the only staged file, `api/invoices.py`, had no leftover conflict markers or whitespace errors.

Because the merge was finished without opening an editor, git kept the `# Conflicts:` lines in the message instead of stripping them. That's normal git behaviour for this case. If you'd rather the message be just the first line, I can run `git commit --amend` to change it.