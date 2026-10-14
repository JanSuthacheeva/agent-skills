Here's the MR. I got the title from ClickUp ticket SHOP-217.

**Title**

```
SHOP-217 Invoices: Export as CSV
```

**Description**

```markdown
## What

Adds a CSV export of invoices that is sent as a file download.

- `billing/export.py`: `export_rows` yields the header row first, then one row per invoice with the columns `number`, `customer`, `issued_at` (ISO 8601) and `total`. `write_csv` writes these rows to any file-like output, using `;` as the separator.
- `api/export.py`: the `export_invoices` endpoint sets `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="invoices.csv"`. It then writes rows straight to the response stream while reading invoices in batches of 500, so memory stays flat for large exports.

## Why

SHOP-217 - users need to export their invoices as CSV.

## Notes for reviewers

- The separator is `;`, not `,`, so the file opens correctly in Excel with German regional settings, where `,` is the decimal separator.
- `total` is written with `str()`, so a decimal value like `1234.50` comes out with a `.` decimal point.

## Testing

- Added `billing/test_export.py::test_header_comes_first`, which checks that the header row comes first and the columns are in the right order.
```

A few things you may want to deal with before opening the MR:

- **Weak tests:** the only test checks the header. Nothing covers the data rows, the `;` separator, or the endpoint's response headers.
- **Unclear `customer` value:** if `invoice.customer` is a model object rather than a string, the CSV will contain whatever that object prints as, not a readable name.
- **No Excel encoding marker:** the file has no byte-order mark (BOM). Without one, Excel may show umlauts wrong even though the response says UTF-8.