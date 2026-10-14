I committed both staged files as one commit, `d20f71d`, on `ECOM-88-drop-currency-param`:

```
api: drop currency query param from invoice endpoint

BREAKING CHANGE: GET /invoices/<id> no longer reads the currency
query parameter. The currency now always comes from the owning
account, so the old parameter could request totals in a currency
we never converted to.

Migration: stop sending currency and read it from the response.

Refs: ECOM-88
```

The README change documents the API change in `api/invoices.py`, so I kept them together. Nothing was pushed.