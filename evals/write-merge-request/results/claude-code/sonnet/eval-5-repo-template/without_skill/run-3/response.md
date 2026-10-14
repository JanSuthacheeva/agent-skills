**Title:** `billing: round invoice totals per line`

**Description** (follows `.gitlab/merge_request_templates/Default.md`):

```markdown
## What

- `invoice_total` in `billing/totals.py` now rounds each line (`qty * price`) to the cent with `ROUND_HALF_UP` and sums the rounded values. Before, it summed the raw products and rounded once at the end.
- Pulled the cent quantum into a `CENT` constant.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent. The accounting export rejected those invoices. The PDF shows rounded line amounts, so the total has to be the sum of those rounded lines.

## Deploy notes

- `GET` invoice responses from `api/invoices.py` use `invoice_total`. The `amount` for some invoices will change by up to 1 cent compared to before. Any client that cached or stored the old amounts may see a mismatch.
- No migration or config change.
- Edge case: for an invoice with no lines, `sum()` returns the int `0` rather than `Decimal("0.00")`. The old code returned a quantized `Decimal`. Check that nothing downstream relies on the type or on two decimal places for empty invoices.

## Checklist

- [ ] Tests added or updated - not done: the repo has no test suite and this MR adds none. A regression test is needed, e.g. a case where per-line and per-invoice rounding differ, such as three lines of 0.333 x 1.
- [ ] Docs updated - not applicable, no docs cover rounding
```

Two things to look at before you open the MR:
- **Empty invoices:** the empty-invoice return type changed. The fix is `Decimal("0.00")` as the `sum` start value. I haven't changed the code.
- **Checklist:** I left both boxes unticked and noted why. Tick them once a test exists.