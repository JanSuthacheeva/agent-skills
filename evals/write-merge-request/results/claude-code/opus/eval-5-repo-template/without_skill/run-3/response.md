**Title:** `billing: round totals per line instead of per invoice`

(Scoped Commits title, since the branch `fix/line-rounding` has no ticket ID.)

```markdown
## What

`invoice_total` in `billing/totals.py` now rounds each line (`qty * price`) to the cent with `ROUND_HALF_UP` and then adds up the rounded lines. Before, it added up the unrounded line amounts and rounded once at the end.

## Why

The PDF invoices round per line. Rounding once per invoice could leave our total up to one cent away from the PDF total, and the accounting export rejected those invoices. With this change, the `amount` returned by the invoice endpoint (`api/invoices.py`) matches the PDF.

## Deploy notes

- No migration or config changes.
- `amount` for existing invoices may change by up to one cent, because it is computed on read. Anything that stored or reconciled earlier totals may show differences of up to one cent.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

I left both checklist boxes unchecked because the branch adds no tests and changes no docs. The repo has no test suite at all, so a small unit test with a multi-line invoice that used to be off by a cent would be worth adding before merging.

The change also has a side effect: an invoice with no lines now returns the integer `0` instead of `Decimal("0.00")`, because `sum()` starts at `0`. Passing `Decimal("0.00")` as the start value to `sum()` would bring back the old behavior. Tell me if you want me to make that fix.