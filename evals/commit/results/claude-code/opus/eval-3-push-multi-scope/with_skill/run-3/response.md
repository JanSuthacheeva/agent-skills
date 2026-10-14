I committed both staged files as one commit (`6bd4be8`) and pushed it to `origin/main`:

```
api, worker: send invoice amounts as integer cents

Breaking: the invoice endpoint and the export payload now use
"amount_cents" (int) instead of "amount" (decimal). Consumers must
read the new field and divide by 100.
```

It's one commit because both files make the same switch from `amount` to `amount_cents`. Anything that reads the old `amount` field will break.

One thing to check: in `worker/export.py:6`, `int(invoice.amount * 100)` cuts off the fraction instead of rounding. If `invoice.amount` is ever a float, the cents can come out one too low (for example, `int(19.99 * 100)` gives 1998). The API side is safe because `invoice_total` returns a `Decimal` rounded to two places. I couldn't tell from the code what type `invoice.amount` is in the worker. If it can be a float, it should be converted to `Decimal` and rounded before turning it into cents.