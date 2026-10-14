I committed the pagination work as d10699f on `feature/invoice-pagination`:

```
api: paginate invoice list endpoint

Pages hold 50 invoices and are selected with the `page` query
parameter, which defaults to 1.
```

It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the tests.

I left `worker/export.py` out. Its only change is a "WIP: try jitter" comment in the export retry loop, which has nothing to do with pagination. It is still modified and uncommitted.

The branch name has no ticket ID, so there is no `Refs:` trailer.