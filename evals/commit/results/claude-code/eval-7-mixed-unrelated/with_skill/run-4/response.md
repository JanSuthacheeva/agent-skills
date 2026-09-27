I committed the pagination work as `4120b35`:

```
api: paginate invoice list endpoint
```

It contains `api/invoices.py` (the new `list_invoices` with `PAGE_SIZE = 50`) and the new test, `api/test_invoices.py`. I didn't run the test. There's no `Refs:` trailer because the branch name has no ticket ID.

I left out `worker/export.py`. It's unrelated to pagination and only adds a comment saying jitter is still a work in progress, so it stays uncommitted.