I committed both staged files (`api/invoices.py` and `README.md`) as one commit, `a5e24f9`, on `ECOM-88-drop-currency-param`. The README edit documents the same API change, so I kept them together.

```
api: take invoice currency from the account

The currency query parameter let clients request totals in a currency
we never converted to, so the response labelled unconverted amounts
with the wrong currency.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response, which now always reflects the account's currency.

Refs: ECOM-88
```

Nothing was pushed.