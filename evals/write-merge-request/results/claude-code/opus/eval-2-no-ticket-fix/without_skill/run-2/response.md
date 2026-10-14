I opened the MR: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `billing: round totals per line instead of per invoice`. The branch name has no ticket ID, so I used the scoped-commit format.
- **Description:** Explains why totals were off: the whole invoice was rounded once, while the PDF rounds each line, so the two could differ by up to a cent and the accounting export rejected them. It then describes the fix, with a small example of the difference (two lines of `1 x 0.005` now total `0.02` instead of `0.01`).
- **Push:** I pushed `fix/line-rounding` to origin first, with upstream tracking set.

Two things worth a look before merging:
- **No tests:** The repo has none, so I haven't run the change. A test for `invoice_total` covering the drift case would be worth adding.
- **Invoice with no lines:** `invoice_total([])` now returns the plain integer `0` instead of `Decimal("0.00")`. Before this change it crashed. If an empty invoice can happen, passing `Decimal("0.00")` as the starting value to `sum` makes it return a proper amount.