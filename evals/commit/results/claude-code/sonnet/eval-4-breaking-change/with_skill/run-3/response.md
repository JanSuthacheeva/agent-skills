I committed both staged files (`README.md` and `api/invoices.py`) as one commit, since the docs and the code change belong together:

```
api: drop currency param from invoice endpoint

The query parameter let clients request totals in a currency we
never converted to. The currency now always comes from the owning
account.

BREAKING CHANGE: GET /invoices/<id> ignores the currency query
parameter. Clients must stop sending it and read currency from the
response instead.

Refs: ECOM-88
```

Nothing was left out. The `Refs: ECOM-88` trailer comes from the branch name.