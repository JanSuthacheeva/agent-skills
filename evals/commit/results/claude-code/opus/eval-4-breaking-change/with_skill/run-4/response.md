I committed the staged changes to `api/invoices.py` and `README.md` as `a3d3e4b` on `ECOM-88-drop-currency-param`. Nothing else was in the working tree, and nothing was pushed.

```
api: drop currency param from invoice endpoint

The currency query parameter let clients request totals in a currency
the amounts were never converted to. The invoice now always uses the
owning account's currency.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response instead.

Refs: ECOM-88
```

This is a breaking change for API clients, so the message says what changed and what clients need to do. The `Refs: ECOM-88` line comes from the branch name.