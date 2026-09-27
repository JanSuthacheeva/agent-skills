The merge is committed as `44c9ba1 Merge branch 'feature/invoice-currency'`, using git's default message. There were no unmerged files or leftover conflict markers.

In your resolution, `api/invoices.py` now takes the currency from `invoice.account.currency`. That drops the `?currency=` request parameter and the `"USD"` fallback that `main` added in "api: default invoice currency to usd". If you meant to keep either one, it needs a follow-up change.

Nothing was pushed.