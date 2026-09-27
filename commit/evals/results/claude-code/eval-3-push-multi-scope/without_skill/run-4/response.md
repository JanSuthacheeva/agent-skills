I committed your staged changes as two scoped commits and pushed both to `origin/main`. `main` now tracks `origin/main`.

- `75560d4 api: return invoice amount in cents`
- `04a93dc worker: export invoice amount in cents`

There was no `/commit` skill available in this session, so I wrote the messages by hand in your Scoped Commits format, with no co-author line.

Two problems in the pushed code:

1. **Amounts can come out one cent short.** `int(x * 100)` cuts off the decimals instead of rounding, so floating-point error loses a cent. For example, `int(19.99 * 100)` gives `1998`. Use `round(x * 100)`, or better, store the amounts as `Decimal` or integer cents from the start. This affects both `api/invoices.py:5` and `worker/export.py:6`.
2. **This breaks existing consumers.** The API response and the export payload both replace the `amount` field with `amount_cents`. Anything reading `amount` from either one will stop working.

Should I fix the rounding in a follow-up commit?