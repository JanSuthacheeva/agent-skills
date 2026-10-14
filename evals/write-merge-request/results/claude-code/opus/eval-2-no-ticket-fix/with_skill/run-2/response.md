I've drafted the MR below and haven't created it yet. There's no ticket ID in the branch name, so the title follows the commit's scope.

**Title**
```
billing: round totals per line instead of per invoice
```

**Description**
```
Invoice totals were rounded once over the whole invoice, so they could be
up to one cent off the PDF totals, and the accounting export rejected
them. Each line is now rounded to the cent before the lines are added up.
```

There's no Deploy section because nothing outside the code changes: no config, migrations or new dependencies. There's no Review section either, since the whole change is 8 lines in `billing/totals.py`.

One thing I noticed: when an invoice has no lines, `invoice_total` now returns the plain number `0` instead of `Decimal("0.00")`. Before this change, an empty invoice crashed instead. That's not a regression, but passing `start=Decimal("0.00")` to `sum` would make it return a `Decimal` every time. I can add that before we open the MR if you want.

Say "push it" when you want me to push the branch and create the MR against `main`.