clickup-axi can't read SHOP-217, so the title uses the scoped-commit format instead of the ticket title.

**Title**

```
billing: add streaming CSV export of invoices
```

**Description**

```
## Summary

Adds a CSV export for invoices, served as a download from the API (SHOP-217).

- `billing/export.py`: `export_rows` yields a header row followed by one row per invoice (number, customer, issued_at, total). `write_csv` writes those rows to any file-like object.
- `api/export.py`: `export_invoices` sets the CSV content type and an `attachment` disposition (`invoices.csv`). It streams the invoices to the response in batches of 500, so the full result set is never held in memory.
- `billing/test_export.py`: checks that the header row comes first.

## Notes for review

- The delimiter is `;`, not `,`. I assume this is for the German Excel locale. Please confirm it matches what the ticket asks for.
- `export_invoices` is not routed anywhere in this MR. The endpoint registration is not part of the diff.
- Test coverage is limited to header order. Data rows and the streaming response are not tested.
```

Two things to check before you post it. The delimiter note is my guess, so correct it if the ticket says something different. The unrouted endpoint is a gap you may want to close in this MR or track in a follow-up.