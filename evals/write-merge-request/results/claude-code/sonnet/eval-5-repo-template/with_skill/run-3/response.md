Template `Default.md` (the only one) is used. No tests or docs were touched, so the boxes stay unticked.

**Title**
```
billing: round totals per line instead of per invoice
```

**Description**
```
## What

Invoice totals are now the sum of each line rounded to the cent (half up), instead of one rounding of the raw sum. Change is in `invoice_total` in `billing/totals.py`.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent, which the accounting export rejected. The PDF shows rounded lines, so the total now adds up from what it displays.

Totals of existing invoices can change by a cent when recomputed.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

Notes:
- There is no ticket ID in the branch name, so no `Refs`.
- I dropped "Deploy notes" because nothing outside the code is needed.
- The sentence "The PDF shows rounded lines" is my inference from the commit message, not something I verified. Confirm it or delete it.
- No test covers the new rounding. Do you want one added before I push?
- I have not pushed or created the MR. Tell me when to.