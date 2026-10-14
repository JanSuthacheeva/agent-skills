Here's the draft. It uses the repo's GitLab template, `.gitlab/merge_request_templates/Default.md`:

---

**Title:** `billing: round totals per line instead of per invoice`

```
## What

`invoice_total` now rounds each line to the cent (half-up) and adds up the rounded lines, instead of rounding the raw sum once.

## Why

The PDF rounds each line, so rounding once per invoice could be up to one cent off the PDF total. The accounting export rejected those invoices.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

---

- I didn't find any deploy steps, so I left out "Deploy notes".
- I left both checklist boxes unticked because the branch changes only `billing/totals.py`: no tests or docs were added.
- The working tree is clean, and there's no open MR for `fix/line-rounding` yet.
- Separate from the description: an invoice with no lines now returns the integer `0`. Before, it raised an `AttributeError`, because `sum` of nothing gives the integer `0` and integers have no `quantize`. Using `sum(..., Decimal("0.00"))` would return a proper `Decimal`. It might be worth fixing and testing before review.

Do you want me to push the branch and create the MR?