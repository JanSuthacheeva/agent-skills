The merge is committed as `67804c5` with git's default message:

```
Merge branch 'feature/invoice-currency'
```

I checked `api/invoices.py` first and found no leftover conflict markers.

Your resolution takes the currency from `invoice.account.currency`, which drops the `?currency=` request parameter and its `"USD"` fallback from main. That fallback was added in "api: default invoice currency to usd". If that's what you meant, nothing else is needed. If you wanted to keep the request override, the merge needs a follow-up fix.