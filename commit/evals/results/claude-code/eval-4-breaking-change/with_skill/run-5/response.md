I committed the two staged files (`api/invoices.py` and `README.md`) as `ea8ff6c` on `ECOM-88-drop-currency-param`:

```
api: drop currency param from invoice endpoint

The currency query parameter let clients request totals in a currency
we never converted to, so the amount was mislabeled. The invoice now
always uses the owning account's currency.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response instead.

Refs: ECOM-88
```

This is a breaking change for API clients, so the body says so and explains what they need to change. Nothing was pushed.