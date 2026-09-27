I finished the merge as `1249be8` on `main`, using git's default message: `Merge branch 'feature/invoice-currency'`.

Before committing I checked `api/invoices.py`, the only conflicted file, and it had no conflict markers left. Your resolution now takes the currency from `invoice.account.currency`. That drops the `?currency=` request parameter and the `"USD"` fallback that `main` had just added in "api: default invoice currency to usd". If you meant to keep a fallback for accounts with no currency set, it needs adding back.

Nothing was pushed.