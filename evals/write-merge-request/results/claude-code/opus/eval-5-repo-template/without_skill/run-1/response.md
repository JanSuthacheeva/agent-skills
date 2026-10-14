**Title:** `billing: round totals per line instead of per invoice`

```markdown
## What

`invoice_total` now rounds each line (qty x price) to the cent with `ROUND_HALF_UP` and then adds up the rounded lines. Before, it added up the unrounded line amounts and rounded once at the end.

## Why

The PDF invoices round per line, so the per-invoice total could be up to one cent off from the PDF. The accounting export rejected those invoices.

## Deploy notes

- `GET` invoice responses (`api/invoices.py`, field `amount`) can change by up to 0.01 for existing invoices whose line amounts have sub-cent fractions. Any consumer that cached or stored the old amounts will see a difference.
- No migrations or config changes.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

I left both checklist items unchecked because the branch adds no tests and no docs. The repo has no tests at all right now.

One more thing: if an invoice has no lines, `invoice_total` returns the int `0` instead of `Decimal("0.00")`. The old code crashed on that case (`int` has no `.quantize`), so nothing gets worse, but it's probably worth fixing before merge with `sum(..., Decimal("0.00"))` plus a test for it. I can add that if you'd like.