Here's the MR for branch `feature/SHOP-217-invoice-csv-export`. I took the title from ticket SHOP-217 in ClickUp.

**Title:** `SHOP-217 Invoices: Export as CSV`

**Description:**

```markdown
## Summary

Adds a CSV export of invoices. Users can download it as a file.

## Changes

- `billing/export.py`: new `export_rows` (yields the header and then one row per invoice) and `write_csv` (writes the rows to any text stream).
  - Columns: `number`, `customer`, `issued_at` (ISO 8601), `total`.
  - The delimiter is `;`, not `,`.
- `api/export.py`: new `export_invoices` handler. It sets `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="invoices.csv"`. It streams the CSV straight into the response, reading invoices in batches of 500, so memory use stays flat for large exports.
- `billing/test_export.py`: test that the header row comes first and the columns are in the expected order.

## Notes for reviewers

- The `;` delimiter was chosen so the file opens correctly in Excel with German/EU locale settings. Please flag it if consumers expect `,`.
- `write_csv` assumes `response.stream` is a text stream.
- Tests only cover the header. Data row formatting and the HTTP handler have no tests yet.

## How to test

1. Call the invoice export endpoint.
2. Check that the browser downloads `invoices.csv`.
3. Open the file and check the header, the `;` delimiter, ISO dates and totals.
```

The Excel reason for the `;` delimiter is my guess - nothing in the code or commits says why it was chosen. Confirm or remove that line before posting. I also haven't checked that `response.stream` accepts text, which is what `csv.writer` writes.