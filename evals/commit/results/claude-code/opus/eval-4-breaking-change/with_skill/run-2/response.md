I committed the staged changes (`api/invoices.py` and `README.md`) as one commit, `f6a1552`, on `ECOM-88-drop-currency-param`:

```
api: drop currency param from invoice endpoint

The param let clients request totals in a currency we never converted
to, so the amount was mislabeled. Currency now always comes from the
owning account.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response instead.

Refs: ECOM-88
```

This is a breaking change, so the message says so and explains how clients should migrate. Nothing was pushed.