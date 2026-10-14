There's no MR open for `fix/line-rounding` yet, so here's a draft against `main`:

**Title**
```
billing: round totals per line instead of per invoice
```

**Description**
```
Invoice totals were rounded once on the summed amount, so they could differ by up to one cent from the PDF totals. The accounting export rejected those invoices. `invoice_total` now rounds each line to the cent (half-up) before summing, which matches the PDF.
```

I left out Review and Deploy: the diff is one file and needs no config or migration. There's no ticket ID in the branch name, so there's no `Refs:` line either.

One thing I noticed in the code: with an empty `lines` list, `sum()` now returns the int `0` instead of a `Decimal`. Before this change, an empty list raised an error instead. You could pass `start=Decimal("0")` to `sum()` if callers expect a `Decimal`.

Should I push the branch and create the MR?