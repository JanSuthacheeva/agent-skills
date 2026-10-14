I committed the staged changes to `api/invoices.py` and `README.md` as `380354b` on `ECOM-88-drop-currency-param`:

```
api: take invoice currency from the account

The currency query parameter let clients request totals in a currency
we never converted to, so the amount was mislabelled.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response instead.

Refs: ECOM-88
```

Nothing else was staged or modified, so nothing was left out. Nothing was pushed.