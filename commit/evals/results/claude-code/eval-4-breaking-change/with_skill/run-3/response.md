I committed the staged changes to `README.md` and `api/invoices.py` as `50e79b9` on `ECOM-88-drop-currency-param`. Nothing was pushed.

```
api: take invoice currency from the account

The currency query parameter only relabeled the amount without
converting it, so clients could receive totals tagged with a currency
they were never calculated in.

BREAKING CHANGE: GET /invoices/<id> no longer accepts the currency
query parameter. Clients must stop sending it and read currency from
the response, which now always holds the account's currency.

Refs: ECOM-88
```