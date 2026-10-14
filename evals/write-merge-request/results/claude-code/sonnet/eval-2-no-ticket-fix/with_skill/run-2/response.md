Title and description (nothing pushed yet):

**Title**
```
billing: round totals per line instead of per invoice
```

**Description**
```
Invoice totals were rounded once over the whole invoice, so they could differ by up to one cent from the PDF, which sums rounded lines. The accounting export rejected those invoices. Totals are now rounded per line and summed.
```

Notes:
- The branch name has no ticket ID, so there is no `Refs:` line and the title uses the scoped-commit form.
- Invoices already exported or stored with the old totals are not recalculated. Say so in the description if a backfill is needed.

Say "push" or "create it" and I'll push `fix/line-rounding` and open the MR against `main`.