I committed both staged files (`README.md` and `api/invoices.py`) as one commit on `ECOM-88-drop-currency-param`:

```
api: invoices: drop currency query parameter

BREAKING CHANGE: GET /invoices/<id> no longer reads the currency
query parameter. The currency always comes from the owning account,
since the parameter let clients request totals in a currency we never
converted to.

Migration: stop sending the currency parameter and read currency
from the response instead.

Refs: ECOM-88
```

I did not run any tests.