**Title:** `billing: round totals per line instead of per invoice`

(The branch name `fix/line-rounding` has no ticket ID, so I used a scoped commit title.)

```markdown
## What

`invoice_total` in `billing/totals.py` now rounds each line (qty * price) to the cent with ROUND_HALF_UP, then sums the rounded lines. Before, it summed the raw products and rounded once at the end.

`api/invoices.py` is the only caller. The `amount` it returns can now differ by up to a cent from the old value on some invoices.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent. The PDFs show rounded per-line amounts, so their sum didn't always match our total. The accounting export rejected those invoices.

Example: two lines of 0.005 each. Old total is 0.01. New total is 0.02, which matches the two rounded lines on the PDF.

## Deploy notes

- No migration or config change.
- Totals for some invoices will change by up to 0.01 compared to before. Any total already stored or exported with the old rounding won't be recalculated.
- For an invoice with no lines, `sum()` now returns the int `0` instead of `Decimal("0.00")`. The API response `amount` would then be `0`, not `0.00`. I haven't checked how consumers handle this, so please confirm before merging (a `Decimal("0")` start value or a final quantize would fix it).

## Checklist

- [ ] Tests added or updated (none yet: the repo has no tests for `invoice_total`)
- [ ] Docs updated (not needed, no docs mention rounding)
```

I left both checklist boxes unticked because no tests were added. Two things to decide before you open the MR:

- **Empty-invoice case:** the empty-lines return type is a real behavior change, as noted above. I'd fix it in this MR.
- **Tests:** a test for the half-cent case would back up the fix.

I can make either change if you want.