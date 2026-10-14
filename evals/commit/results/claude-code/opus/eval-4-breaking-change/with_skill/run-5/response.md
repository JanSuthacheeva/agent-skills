I committed the staged changes as `a02efa1` on `ECOM-88-drop-currency-param`:

```
api: take invoice currency from the account

The currency query parameter let clients request totals in a currency
we never converted to, so responses mislabeled the amount.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response, which now always reflects the account's currency.

Refs: ECOM-88
```

The `api/invoices.py` change and the README note describe the same change, so they went into one commit. Nothing was left unstaged.