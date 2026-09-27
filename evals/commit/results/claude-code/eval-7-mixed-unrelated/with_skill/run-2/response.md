I committed the pagination work as `6646322`:

```
api: paginate invoice list endpoint
```

- **Included:** `api/invoices.py` (the new `list_invoices` with 50 items per page) and the new test `api/test_invoices.py`. I didn't run the test before committing.
- **Left out:** your change to `worker/export.py`. It's a "WIP: try jitter here" comment in the export retry code and isn't part of the pagination work, so it's still uncommitted.
- **No `Refs:` line:** the branch name `feature/invoice-pagination` doesn't contain a ticket ID.