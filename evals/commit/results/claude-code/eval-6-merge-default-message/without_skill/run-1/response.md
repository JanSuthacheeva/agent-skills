I finished the merge as commit `fee5566`, with the message `api: merge branch 'feature/invoice-currency'`.

- I checked for leftover conflict markers first and found none. `api/invoices.py` now takes the currency from `invoice.account.currency` (the feature branch's version).
- That means main's recent `?currency=` query parameter with the USD fallback is gone.
- I used the Scoped Commits format instead of Git's default "Merge branch ..." message. This repo had no earlier merge commits to copy a style from.
- The `/commit` skill isn't available in this session, so I committed with git directly.
- I didn't run any tests.