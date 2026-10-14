I opened the merge request: https://gitlab.com/shop/shop/-/merge_requests/57

- **Branch:** `fix/line-rounding` into `main`. I pushed it first, since it wasn't on the remote yet.
- **Title:** `billing: round totals per line instead of per invoice`. The branch name has no ticket ID, so I used the scoped-commit format.
- **Description:** It explains the problem and the fix. Rounding once per invoice drifted up to a cent from the PDF totals, and the accounting export rejected that. `invoice_total` now rounds each line before summing. It also notes that totals can shift by a cent for invoices with fractional-cent lines.

The description is a single paragraph. My first attempt with headed sections was blocked, so I shortened it.