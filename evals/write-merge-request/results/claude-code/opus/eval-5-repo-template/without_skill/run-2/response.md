**Title:** `billing: round totals per line instead of per invoice`

(The branch `fix/line-rounding` has no ticket ID, so I used the Scoped Commits format.)

```markdown
## What

`invoice_total` now rounds each line (`qty * price`) to the cent, using `ROUND_HALF_UP`, before adding the lines up. Before, it added up the unrounded line amounts and rounded the invoice total once at the end.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent, and the accounting export rejected those invoices. Rounding each line the same way the PDF does makes the totals match.

## Deploy notes

- Totals are calculated on request, not stored. After deploy, `amount` in the invoice endpoint (`api/invoices.py`) can change by up to 0.01 for existing invoices, including ones that were already exported or sent.
- No migration or config changes.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

The repo has no tests, so I left both checklist boxes unticked. A test with lines whose rounded and unrounded sums differ would be worth adding before merge, for example 3 lines of `qty=1, price=0.005`: the old code gives 0.02, the new code gives 0.03.

An invoice with no lines also behaves differently now. It used to crash with `AttributeError` (`0.quantize`). It now returns the plain integer `0`, not a `Decimal`. If that matters, use `sum(..., Decimal("0.00"))`.