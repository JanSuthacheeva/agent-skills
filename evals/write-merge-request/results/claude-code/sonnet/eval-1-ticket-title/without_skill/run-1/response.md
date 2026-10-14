I couldn't read ticket SHOP-217 from ClickUp. `clickup-axi` returns "not found" for every form of the ID I tried. So the title uses the scoped-commit format instead of the ticket title.

**Title**

```
billing: add CSV export of invoices
```

**Description**

```markdown
## What

Adds a CSV export for invoices, with an API endpoint that streams it as a download.

- `billing/export.py`: `export_rows` yields the header row (`number`, `customer`, `issued_at`, `total`) followed by one row per invoice. `write_csv` writes those rows to any file-like object.
- `api/export.py`: `export_invoices` sets `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="invoices.csv"`. It streams the rows straight into the response, reading invoices in batches of 500 so large exports are not held in memory.
- `billing/test_export.py`: checks that the header row comes first.

## Notes for review

- The CSV uses `;` as the delimiter, not `,`. Please confirm this is what consumers expect (e.g. Excel in a German locale). It is a one-line change in `write_csv` if not.
- `issued_at` is written as ISO 8601 and `total` as `str(invoice.total)`, so the decimal formatting is not locale-specific.
- `export_invoices` is not yet wired to a route in this branch.

## Testing

- Added a unit test for header order.
- Not covered: the streaming endpoint (headers and batching) and the data rows themselves.
```

I left out the ticket link because I couldn't confirm the ticket. Add `SHOP-217` to the description if your MR template needs it. If you can get the ticket title, I'll switch the MR title to `SHOP-217 <ticket title>`.

I also wrote "not yet wired to a route" from the diff alone, since I didn't search the rest of the repo for one. Please check that line before posting.