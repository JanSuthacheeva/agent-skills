**Title**

```
billing: round totals per line instead of per invoice
```

**Description** (follows `.gitlab/merge_request_templates/Default.md`)

```
## What

`invoice_total` now rounds each line to the cent (half up) and sums the rounded lines. Before, it summed the raw amounts and rounded once at the end.

## Why

Rounding once per invoice made totals differ from the PDF totals by up to one cent, and the accounting export rejected those invoices.

## Checklist

- [ ] Tests added or updated
- [ ] Docs updated
```

Notes:
- I dropped "Deploy notes" because the change is code-only. There's no ticket ID in the branch name, so there's no `Refs:` line.
- I left both checklist boxes unticked because the branch doesn't add tests or update docs.
- **Possible bug:** with an empty `lines` list, `invoice_total` now returns the integer `0` instead of `Decimal("0.00")`. Before, the sum went through `.quantize()`, which turned it into a Decimal. Passing `Decimal("0.00")` as the start value to `sum(...)` would fix this. A test for a case where per-line rounding gives a different total would also be worth adding.
- There's no open MR for `fix/line-rounding` yet. Tell me to push and I'll create it against `main`.