Title is from ticket SHOP-217 in ClickUp. There's no MR template and no open MR for this branch.

```
SHOP-217 Invoices: Export as CSV
```

```
The accounting team needs invoices in a spreadsheet. Invoices can now be
downloaded as a CSV file with number, customer, issue date and total.

- The file is streamed: invoices are loaded 500 at a time and each row is
  written straight to the response, so exporting 50,000 invoices does not
  hold them all in memory.
- The separator is a semicolon, not a comma, because the accounting team
  opens the file in German Excel, which reads commas as decimal marks.

Refs: SHOP-217
```

I left out the Review and Deploy sections. The diff is only 23 lines, and it adds no environment variables, migrations or dependencies.

Three things in the diff you may want to check before review. I left them out of the description because the commits don't say what you intended:

- **Decimal point in totals:** `str(invoice.total)` writes totals like `123.45`. German Excel expects `123,45`, so it may read these as dates or text. That works against the reason for using semicolons.
- **Encoding:** the file is UTF-8 without a BOM. German Excel usually opens such files as Windows-1252, so umlauts in customer names may come out garbled.
- **Route:** `api/export.py` adds `export_invoices`, but this branch doesn't register it with any route. If routes aren't picked up automatically, the endpoint can't be reached.

Tell me if you want me to push the branch and create the MR.