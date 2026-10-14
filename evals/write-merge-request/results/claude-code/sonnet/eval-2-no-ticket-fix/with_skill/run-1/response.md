Branch `fix/line-rounding` has no ticket ID, so the title uses the scoped-commit format. There is no template and no open MR. Nothing is pushed yet.

**Title**
```
billing: round totals per line instead of per invoice
```

**Description**
```
Invoice totals were rounded once over the sum, which drifted from the PDF's per-line totals by up to one cent, and the accounting export rejected those invoices. `invoice_total` now rounds each line to the cent and sums the rounded values.

Existing invoices recomputed with this change can differ by a cent from totals stored before it.
```

I left the last sentence in because it follows from the diff. If it's wrong, for example because totals are never recomputed, drop it.

Tell me to push and create the MR when you want it.