Here's a draft MR title and description for `feature/SHOP-217-invoice-csv-export`. I took the title from ticket SHOP-217 in ClickUp.

**Title**

```
SHOP-217 Invoices: Export as CSV
```

**Description**

```markdown
## Summary

Adds a CSV export of invoices, served as a file download from the API.

## Changes

- `billing/export.py`: `export_rows` yields a header row (`number`, `customer`, `issued_at`, `total`) followed by one row per invoice. `write_csv` writes these rows to any file-like output.
- `api/export.py`: `export_invoices` sets `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="invoices.csv"`, then streams invoices into the response in batches of 500. The full export is never loaded into memory.
- `billing/test_export.py`: checks that the header row comes first and that the columns are in the right order.

## Notes for reviewers

- The delimiter is `;`, not `,`. This lets German-locale Excel open the file without an import step, but anything that expects comma-separated input will need adjusting.
- `issued_at` is written in ISO 8601 format, and `total` is written with `str()`, so it keeps a `.` as the decimal separator.
- There's no BOM, so Excel may show non-ASCII customer names incorrectly.

## Testing

- `pytest billing/test_export.py`
```

The description doesn't say where `export_invoices` is wired into the routes, because the diff doesn't show that. The only test covers the header row, not the data rows or the API handler. You may want to add tests for those before merging.