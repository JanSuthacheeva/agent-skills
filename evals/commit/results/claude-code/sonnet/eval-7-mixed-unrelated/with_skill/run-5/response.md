I committed the pagination work as ff0d198:

```
api: paginate invoice list endpoint

Pages hold 50 invoices and are selected with the `page` query
parameter, which defaults to 1.
```

It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the tests.

I left out `worker/export.py`. Its only change is an unfinished "WIP: try jitter" comment in the retry loop, which has nothing to do with pagination. It's still modified in your working tree.

The branch name has no ticket ID, so there's no `Refs:` trailer.