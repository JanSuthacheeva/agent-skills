I opened the MR: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `billing: round totals per line instead of per invoice`. The branch name has no ticket ID, so I used the scoped-commit format.
- **Branch:** I pushed `fix/line-rounding` to origin and set it to track the remote. The MR targets `main`.
- **Description:** It says why the change was needed: invoice totals could differ from the PDF by up to one cent, and the accounting export rejected them. It says what changed: each line is now rounded to the cent before summing. It also warns that some invoice totals will shift by up to a cent, which is intended.

One thing I noticed while reading the diff: for an invoice with no lines, `invoice_total([])` now returns the plain integer `0` instead of `Decimal("0.00")`. Before this change, the same call crashed. It's an edge case, but passing `Decimal("0")` as the start value to `sum` would make the return type consistent. I can add that to this MR if you want.