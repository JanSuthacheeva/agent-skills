No open MR exists for this branch. Here is the draft. Nothing is pushed yet.

**Title**
```
billing: round totals per line instead of per invoice
```

**Description**
```
Invoice totals were rounded once on the sum, so they could drift by up to one cent from the PDF, which rounds per line. The accounting export rejected those invoices. `invoice_total` now rounds each line to the cent (half up) before summing.

- Totals of existing invoices can change by a cent when they are recomputed, because the rounding point moved. That is the intended fix, since it now matches the PDF.
```

I left out Review, Deploy and Refs. The diff is one small hunk, there is nothing to deploy, and the branch name has no ticket ID.

Should I push the branch and create the MR?