I committed the staged changes as one commit (3ff7e6f) on `ECOM-88-drop-currency-param`. The README update went in with the code change it documents.

```
api: drop currency query param from invoice endpoint

The parameter let clients request totals in a currency we never
converted to. The currency now always comes from the owning account.

BREAKING CHANGE: GET /invoices/<id> no longer reads the currency
query parameter. Clients must stop sending it and read currency from
the response instead.

Refs: ECOM-88
```