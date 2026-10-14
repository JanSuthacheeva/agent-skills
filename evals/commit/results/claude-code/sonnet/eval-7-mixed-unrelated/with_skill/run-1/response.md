I committed the pagination work as `3a55696` on `feature/invoice-pagination`:

```
api: paginate invoice list endpoint

Pages hold 50 invoices and are selected with the `page` query
parameter.
```

I did not run the tests. The commit has `api/invoices.py` and the new `api/test_invoices.py`.

I left `worker/export.py` out. Its only change is an unfinished "WIP: try jitter" comment, which has nothing to do with pagination.

The branch name has no ticket ID, so there is no `Refs:` trailer.