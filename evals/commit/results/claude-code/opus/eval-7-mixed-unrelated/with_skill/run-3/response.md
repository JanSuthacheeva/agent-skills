I committed the invoice list pagination as `85cdcd4`, with the message:

```
api: paginate invoice list endpoint
```

The commit has `api/invoices.py` and the new test file `api/test_invoices.py`. I didn't run the test.

I left `worker/export.py` out. Its only change is an unrelated comment marked "WIP: try jitter here, not done yet", so it's still uncommitted.

There's no `Refs:` line because the branch name `feature/invoice-pagination` has no ticket ID.