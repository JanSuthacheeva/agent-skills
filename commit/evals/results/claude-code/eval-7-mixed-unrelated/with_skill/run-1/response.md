I committed the pagination work as `e13e0b5`:

```
api: paginate invoice list endpoint
```

It includes `api/invoices.py` (the new `list_invoices`, 50 items per page) and the new test `api/test_invoices.py`. I didn't run the test before committing. There's no `Refs:` trailer because the branch name has no ticket ID.

I left out `worker/export.py`. Its only change is an unfinished comment ("WIP: try jitter here, not done yet") that has nothing to do with pagination, so it's still uncommitted.