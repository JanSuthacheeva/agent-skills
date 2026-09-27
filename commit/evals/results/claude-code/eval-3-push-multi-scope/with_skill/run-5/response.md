I committed the change and pushed it to `origin/main` as `e070b8d`. `main` had no upstream branch, so I set it to track `origin/main`.

```
api, worker: send invoice amounts as integer cents

Breaking: the invoice endpoint and the export payload now use
amount_cents (int) instead of amount. Consumers must read
amount_cents and divide by 100 for the major unit.
```

There's no `Refs:` line because the branch name contains no ticket ID.

**There's a bug in what I just pushed:** `int(x * 100)` cuts off decimals instead of rounding, and float math is slightly off. So an amount of 19.99 becomes 1998 cents, not 1999. This happens in both `api/invoices.py` and `worker/export.py`. The fix is to use `round(x * 100)`, or better, to work in `Decimal` or integer cents from the start in `billing.totals`. Do you want me to fix it in a follow-up commit?