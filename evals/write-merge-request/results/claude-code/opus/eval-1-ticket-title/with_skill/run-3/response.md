No open MR exists for this branch yet. Here's the draft:

```
SHOP-217 Invoices: Export as CSV

Invoices can now be downloaded as a CSV file. The export streams one row
at a time, from the database to the response.

- Rows are generated one by one and written straight to the response, and
  invoices are fetched in batches of 500. Exporting 50,000 invoices
  therefore never holds them all in memory.
- The separator is a semicolon, not a comma. The accounting team opens the
  file in German Excel, which reads commas as decimal marks.

Refs: SHOP-217
```

I left out the review and deploy sections. The diff is only 23 lines, and there are no new environment variables, migrations or dependencies.

Two things in the code you may want to check before review:
- **Decimal marks:** `str(invoice.total)` writes totals with a dot, like `12.50`. German Excel may read these as text or dates instead of numbers. Since German Excel is the reason for the semicolons, totals probably need a comma too.
- **No route:** the branch doesn't register `api/export.py` `export_invoices` with any route. If that happens somewhere else, ignore this.

Say the word and I'll push the branch and create the MR.