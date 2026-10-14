I finished the merge on `main` as commit `916eb5a`, using git's default message:

```
Merge branch 'feature/invoice-currency'
```

Before committing, I checked `api/invoices.py` for leftover conflict markers and found none. Afterwards the working tree was clean.

The first commit kept the commented `# Conflicts:` lines in its message, because finishing a merge without opening the editor doesn't strip comments. I amended it to just the default subject line. It's still a proper merge commit with both parents, and nothing was pushed.