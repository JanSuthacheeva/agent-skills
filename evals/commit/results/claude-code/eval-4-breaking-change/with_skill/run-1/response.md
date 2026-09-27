I committed the staged `README.md` and `api/invoices.py` changes together as `caa220a` on `ECOM-88-drop-currency-param`, since the README update documents the API change. Nothing else was staged or left out.

```
api: take invoice currency from the account

The currency query parameter let clients request totals in a currency
we never converted to, so the returned amount was mislabeled.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response, which now reflects the account's currency.

Refs: ECOM-88
```