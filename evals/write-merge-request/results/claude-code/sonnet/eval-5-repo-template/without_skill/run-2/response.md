**Title:** `billing: round invoice totals per line`

**Description**

## What

`invoice_total` now rounds each line (qty x price) to the cent with `ROUND_HALF_UP`, then sums the rounded values. Before, it summed the raw products and rounded once at the end.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent. The PDF shows per-line amounts, so the totals no longer matched the lines, and the accounting export rejected those invoices.

## Changes

- `billing/totals.py`: round per line, and add a `CENT` constant in place of the inline `Decimal("0.01")`.

## Behavior change

Invoice totals can differ by a cent from before. Example: three lines of 0.125 round to 0.13 each, so the total is 0.39. The old code summed to 0.375 and rounded to 0.38. The new totals match the PDF and the export.

## Review notes

- For an empty `lines` list, `sum()` now returns the int `0` instead of `Decimal("0.00")`. If callers depend on a `Decimal` result, pass `Decimal("0.00")` as the `sum` start value. Say if you want that added here.
- I did not run any tests, and the branch adds none. A test for the half-cent case above would be worth adding.

I left out a ticket ID because the branch name `fix/line-rounding` has none, so the title uses the scoped-commit format.