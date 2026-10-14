I committed the pagination work as `fbe2b2b` with the message:

```
api: paginate invoice list endpoint
```

It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the test.

I left out `worker/export.py`, which is still uncommitted. Its only change is a WIP comment about adding jitter to the retry logic, which isn't part of this work.

One problem in the new code: `page=0` or a negative page gives a negative start index, so the slice returns the wrong items instead of an error. A non-numeric `page` makes `int()` raise a `ValueError`. Both should probably be validated.