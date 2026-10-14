No open MR exists for `fix/line-rounding`. Here's the draft, targeting `main`:

**Title**

```
billing: round totals per line instead of per invoice
```

**Description**

```
Invoice totals were rounded once over the whole invoice, so they could be one cent off the PDF totals, which round each line. The accounting export rejected those invoices. `invoice_total` now rounds each line to the cent (half-up) before adding them up.
```

I left out a review guide and deploy steps: it's one commit with a 6-line diff, and nothing changes outside the code.

One thing I noticed in the code: if an invoice has no lines, `invoice_total([])` now returns the integer `0` instead of a `Decimal`. Before this change, the same input crashed, because an integer has no `.quantize`. You could pass a start value, `sum(..., Decimal("0"))`, to fix that in this MR.

Should I push the branch and create the MR?