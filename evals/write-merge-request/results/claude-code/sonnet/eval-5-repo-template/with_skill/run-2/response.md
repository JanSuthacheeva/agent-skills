**Title**

```
billing: round totals per line instead of per invoice
```

**Description** (uses `.gitlab/merge_request_templates/Default.md`; "Deploy notes" is dropped because nothing needs deploying)

```
## What

Invoice totals are now the sum of each line rounded to the cent, instead of the sum of the raw line amounts rounded once at the end. The change is in `invoice_total` in `billing/totals.py`.

## Why

Per-invoice rounding drifted from the PDF totals by up to one cent, which the accounting export rejected. The PDF totals are per line, so the total now matches them.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

I left both checklist boxes unticked because the branch changes only `billing/totals.py`, with no tests or docs.

There's no open MR for this branch and the working tree is clean. I haven't pushed anything. Tell me to push and create it, and I'll run `git push -u origin fix/line-rounding` and `glab mr create` against `main`.