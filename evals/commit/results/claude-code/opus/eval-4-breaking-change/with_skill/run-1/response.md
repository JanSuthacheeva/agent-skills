I committed the staged changes in `README.md` and `api/invoices.py` as `c4cb696` on `ECOM-88-drop-currency-param`:

```
api: drop currency query param from invoice endpoint

The parameter let clients request totals in a currency we never
converted to, so the response could mislabel the amount. The currency
now always comes from the owning account.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients that sent it must drop it and read currency
from the response instead.

Refs: ECOM-88
```

My first version of this commit said the response could label EUR amounts as another currency. Nothing in the diff shows the amounts are always EUR, so I amended the message to the wording above. Nothing was pushed.