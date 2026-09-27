I committed the staged changes as `66c9f35` and pushed them to `origin/main`. `main` had no upstream branch, so it now tracks `origin/main`.

```
api, worker: send invoice amounts as integer cents

Float amounts are prone to rounding errors. Both the invoice endpoint
and the export payload now use an integer amount_cents field.

BREAKING CHANGE: the invoice endpoint and export payload replace
"amount" with "amount_cents". Consumers must read the new field and
divide by 100 for the major-unit value.
```

- **Breaking change:** anything that reads `amount` from the invoice endpoint or the export payload will break until it switches to `amount_cents`.
- **Commit message wording:** the reason in the body ("float amounts are prone to rounding errors") is my guess from the diff, not something you told me.
- **Likely bug:** `int(x * 100)` cuts off the decimal part instead of rounding. For example, `int(0.29 * 100)` gives `28`, not `29`, so some amounts will come out one cent short. Using `round(x * 100)` or `Decimal` would fix this. I can make that change if you want.