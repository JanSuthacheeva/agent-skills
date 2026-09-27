I committed both files and pushed to `origin/main`: `3523761 api, worker: send invoice amounts as integer cents`.

- **One commit for both files:** the API and worker changes are the same switch to integer cents, so I kept them together rather than splitting by scope.
- **No `/commit` skill:** your instructions say to use it, but it isn't available in this session. I wrote the message by hand, matching the `<scope>: <description>` style in the history.
- **Pushed straight to `main`:** that's how the history already looks, but it goes against the usual "never commit to main" convention.

**Rounding bug in what I pushed:** `int(x * 100)` cuts off decimals instead of rounding, so float errors lose a cent. For example, `int(0.29 * 100)` gives `28`, not `29`. This happens in both `api/invoices.py:5` and `worker/export.py:6`. The fix is `round(x * 100)`, or better, working in `Decimal` or integer cents inside `billing.totals`. Want me to fix it in a follow-up commit?