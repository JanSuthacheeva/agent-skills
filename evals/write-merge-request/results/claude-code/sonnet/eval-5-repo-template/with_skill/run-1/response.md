Here is the MR text. I haven't pushed or created anything. There is no open MR for this branch, and the repo's `Default.md` template is used.

**Title**

```
billing: round totals per line instead of per invoice
```

**Description**

```
## What

`invoice_total` now rounds each line to the cent (half up) and sums the rounded lines, instead of rounding the raw sum once.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent, which the accounting export rejected.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

- I dropped "Deploy notes" because the diff has no migrations, config or dependency changes.
- I left both checklist boxes unticked because the branch changes only `billing/totals.py`. It has no test or docs changes, and a rounding fix like this probably wants a test.
- The branch name has no ticket ID, so there is no `Refs:` line.

Say "create it" and I'll push and open the MR.