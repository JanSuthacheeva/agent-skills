I committed the staged changes as one commit, `d52c5b7`, on `ECOM-88-drop-currency-param`:

```
api: drop currency query param from invoice endpoint

The param let clients request totals in a currency we never
converted to. The response now always uses the owning account's
currency.

BREAKING CHANGE: GET /invoices/<id> ignores the currency query
parameter. Clients must stop sending it and read currency from the
response instead.

Refs: ECOM-88
```

The code change in `api/invoices.py` and the README note describe the same change, so I kept them in one commit. I didn't run any tests.