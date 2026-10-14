I committed the pagination work as `477daad`:

```
api: paginate invoice list endpoint
```

The commit includes `api/invoices.py` (the new `list_invoices` with 50 items per page) and the new test file `api/test_invoices.py`. I didn't run the test.

I left `worker/export.py` out. Its only change is a `# WIP: try jitter here, not done yet` comment, which has nothing to do with pagination, so it's still uncommitted.