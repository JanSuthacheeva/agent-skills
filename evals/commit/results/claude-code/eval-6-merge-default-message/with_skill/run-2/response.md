I've finished the merge. `feature/invoice-currency` is now merged into `main` as `65861a7`, with git's default message:

```
Merge branch 'feature/invoice-currency'
```

Before committing I checked for leftover problems: no files were still marked as conflicted and no conflict markers were left. The only file in the merge commit is your resolution of `api/invoices.py`. The working tree is clean, and nothing was pushed.

After committing I amended the merge once to fix its message. Committing without the editor had left git's `# Conflicts:` comment lines in it, which the editor would normally remove.