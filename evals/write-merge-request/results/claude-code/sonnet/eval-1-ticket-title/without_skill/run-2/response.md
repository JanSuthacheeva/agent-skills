**Title**

```
billing: add CSV export of invoices
```

I couldn't read ticket SHOP-217 with clickup-axi (it returns "task not found"), so the title uses the scoped-commit format instead of `SHOP-217 <ticket title>`. If you have the ticket title, swap it in as `SHOP-217 <title>`.

**Description**

```markdown
## What

Adds a CSV export of invoices and an API endpoint that serves it as a download.

- `billing/export.py`: `export_rows` yields a header row (`number`, `customer`, `issued_at`, `total`) followed by one row per invoice. `write_csv` writes those rows to any file-like object.
- `api/export.py`: `export_invoices` sets the `text/csv` content type and an `attachment; filename="invoices.csv"` disposition. It streams the invoices to the response in batches of 500, so the full result set is never held in memory.
- `billing/test_export.py`: checks that the header row comes first.

## Notes for review

- The delimiter is `;`, not `,`. I assumed this is for German-locale Excel. Please confirm that is intended.
- `issued_at` is written as ISO 8601 and `total` as `str(invoice.total)`, so no currency formatting is applied.
- `export_invoices` is not wired to a route in this diff.

## Testing

- Added a unit test for header ordering.
- There are no tests yet for the row contents, the `;` delimiter, or the streaming endpoint.

Refs: SHOP-217
```