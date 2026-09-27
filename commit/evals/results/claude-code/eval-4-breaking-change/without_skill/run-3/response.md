I committed the staged changes to `ECOM-88-drop-currency-param` as `86da5e4`:

```
api: invoices: drop currency query parameter

GET /invoices/<id> now always returns the owning account's currency.
The currency query parameter let clients request totals in a currency
the amount was never converted to, so the response could be wrong.

BREAKING CHANGE: the currency query parameter is removed. Clients that
sent it must drop it and read currency from the response instead.
```

- I used the `api: invoices:` scope to match the repo's existing nested scopes (e.g. `api: auth:`).
- The `BREAKING CHANGE:` footer is there because removing the query parameter changes the public API.
- The working tree is clean, and nothing has been pushed.