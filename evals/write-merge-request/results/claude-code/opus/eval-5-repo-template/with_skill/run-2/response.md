No open MR exists for `fix/line-rounding`. The repo has a GitLab template (`.gitlab/merge_request_templates/Default.md`), so the description follows its headings.

**Title**

```
billing: round totals per line instead of per invoice
```

**Description**

```
## What

Invoice totals are now built by rounding each line to the cent first and then adding the lines up. Before, the raw amounts were added up and only the final sum was rounded.

## Why

The invoice PDF rounds each line, so rounding only the final sum could make the total differ from the PDF by up to one cent. The accounting export rejects invoices with that difference.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

I left out "Deploy notes" because nothing needs doing outside the code. I left both checklist boxes unticked because the branch has no test or docs changes.

Two things to consider before opening it:
- **No test covers this.** A regression test with lines whose rounding differs between the two methods would be worth adding.
- **Invoices with no lines.** `invoice_total([])` now returns the plain number `0` instead of a decimal amount. Before this change it crashed instead. If empty invoices can happen, starting the sum at `Decimal("0.00")` would make it return a proper amount.

Tell me when to push the branch and create the MR.