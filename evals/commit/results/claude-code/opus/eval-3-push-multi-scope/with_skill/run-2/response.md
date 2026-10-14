I committed the change and pushed it to `origin/main`:

```
api, worker: report invoice amounts as integer cents

Breaking: the invoice endpoint and the export payload now send
"amount_cents" (int) instead of "amount" (float). Consumers must
read the new field and divide by 100 for the major unit.
```

The `/commit` skill never pushes, so I ran the push myself because you asked for it. `main` had no upstream branch, so the push also set it to track `origin/main`.

**This change has a rounding bug:** `int(x * 100)` cuts off the decimals instead of rounding. Because of how floats work, `int(19.99 * 100)` gives `1998`, so some amounts will come out one cent short. Both places that build the field have this problem: `api/invoices.py:5` and `worker/export.py:6`. The fix is to use `round(x * 100)`, or better, to do the math in `Decimal` or whole cents throughout. Want me to fix it?