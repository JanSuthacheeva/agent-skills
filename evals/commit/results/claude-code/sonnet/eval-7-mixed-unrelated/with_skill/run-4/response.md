I committed the pagination work as f3cd577 on `feature/invoice-pagination`:

```
api: paginate invoice list endpoint

Pages are fixed at 50 items and selected with the page query
parameter.
```

It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the tests. The branch name has no ticket ID, so there's no `Refs:` trailer.

I left `worker/export.py` out. Its only change is an unfinished "WIP: try jitter" comment, which has nothing to do with pagination. It is still modified in your working tree.