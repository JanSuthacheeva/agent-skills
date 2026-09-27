I committed the staged changes as `aa56bd3` on `ECOM-88-drop-currency-param`, covering `api/invoices.py` and `README.md`. Both files were already staged and nothing else was changed.

```
api: drop currency param from invoice endpoint

The param let clients request totals labelled in a currency we never
converted to, so the amount and currency could disagree. The currency
now always comes from the owning account.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency query
parameter. Clients must stop sending it and read currency from the
response instead.

Refs: ECOM-88
```

This breaks the API for clients that send the `currency` parameter, so the message says what they need to change.