I finished the merge on `main` as commit `2fdd4a4`, using git's default message:

```
Merge branch 'feature/invoice-currency'
```

Before committing, I checked that nothing was still marked as conflicted and that no conflict markers were left. The only change in it is your fix in `api/invoices.py`.

Because I committed without opening an editor, git kept its `# Conflicts: api/invoices.py` note in the message body. It would normally remove that note when you save the message in an editor. If you want it gone, run `git commit --amend` and save.