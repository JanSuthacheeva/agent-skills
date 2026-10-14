I committed the pagination work as `4e5ca92` with the message:

```
api: paginate invoice list endpoint
```

The commit has the changes to `api/invoices.py` and the new test in `api/test_invoices.py`. I didn't run the test.

I left `worker/export.py` uncommitted because it isn't part of the pagination work. Its only change is a comment marked as unfinished: `# WIP: try jitter here, not done yet`.

There's no `Refs:` line because the branch name, `feature/invoice-pagination`, doesn't include a ticket ID.