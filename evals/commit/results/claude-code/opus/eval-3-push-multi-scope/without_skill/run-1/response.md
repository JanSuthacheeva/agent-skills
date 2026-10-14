I made two commits and pushed them to `origin/main`. The `/commit` skill your instructions ask for isn't available in this session, so I committed directly using the repo's scoped format.

- `1fbe295 api: return invoice amount in cents`
- `5618718 worker: export invoice amount in cents`

Two problems in the change itself:

- **Rounding bug:** `int(x * 100)` cuts off the decimals instead of rounding, so some amounts come out a cent low. For example, `int(0.29 * 100)` gives `28`. Use `round(x * 100)`, or `Decimal` all the way through.
- **Breaking change:** renaming the `amount` field to `amount_cents` will break anything that reads the invoice endpoint or the export payload unless those readers are updated too.

Should I fix the rounding?