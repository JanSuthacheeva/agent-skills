I opened the merge request: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `billing: round totals per line instead of per invoice`. The branch name has no ticket ID, so I used a scoped-commit title.
- **Target:** `main`. I pushed `fix/line-rounding` to origin first.
- **Description:** It explains why, what changed and what to expect:
  - **Why:** rounding once per invoice drifted from the PDF totals by up to a cent, and the accounting export rejected those invoices.
  - **What:** `invoice_total` in `billing/totals.py` now rounds each line to the cent before summing.
  - **Expect:** totals can shift by a cent on invoices with fractional-cent lines, and the change adds no tests.

I didn't run any tests, and the change doesn't include any. A regression test for a fractional-cent invoice would be worth adding.