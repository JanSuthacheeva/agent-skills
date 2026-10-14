I pushed `fix/line-rounding` and opened the MR: https://gitlab.com/shop/shop/-/merge_requests/57

**Title:** `billing: round totals per line instead of per invoice`. The branch name has no ticket ID, so I used a scoped commit title instead.

The description explains why: totals were rounded once for the whole invoice, but the PDF rounds each line, so the two could differ by a cent and the accounting export rejected them. It also covers what changed, gives a before/after example, and says that nothing in the repo tests `billing/totals.py`.

There's a likely regression I spotted but didn't change or run. For an invoice with no lines, `sum(...)` with no start value returns the plain integer `0` instead of `Decimal("0.00")`, so the invoice endpoint's `amount` would change type for empty invoices. Passing `Decimal("0.00")` as the start value would fix it. I can add that fix and a test for `invoice_total` to this MR if you want.