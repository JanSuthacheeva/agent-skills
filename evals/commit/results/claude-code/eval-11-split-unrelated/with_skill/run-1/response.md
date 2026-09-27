The three changes weren't related, so I made three commits on `main`. The working tree is now clean.

1. `billing: use banker's rounding for invoice totals` (`billing/totals.py`, `ROUND_HALF_UP` to `ROUND_HALF_EVEN`)
2. `worker: raise export retries from 3 to 5` (`worker/export.py`)
3. `docs: describe the service in readme` (`README.md`)

None of them has a body because I don't know why you made these changes. The rounding change affects invoice totals: an amount exactly halfway, like 0.125, now rounds to 0.12 instead of 0.13. If there's a reason behind it, such as matching the accounting export, it would be worth adding to that commit's message. Nothing was pushed.