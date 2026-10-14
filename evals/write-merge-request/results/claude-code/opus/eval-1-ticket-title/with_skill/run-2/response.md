I didn't find an existing MR for this branch, and the working tree is clean.

**Title**

```
SHOP-217 Invoices: Export as CSV
```

**Description**

```
Invoices can now be downloaded as a CSV file with number, customer, issue
date and total.

- Rows are generated one at a time and written straight to the response, and
  invoices are read in batches of 500. Exporting 50,000 invoices therefore
  does not hold them all in memory.
- The separator is a semicolon instead of a comma. The accounting team opens
  the file in German Excel, which reads commas as decimal marks.

Refs: SHOP-217
```

I left out a review section because the diff is only 23 lines. There's nothing to deploy: no new environment variables, migrations or dependencies.

Two things to check before review. Both come from opening the file in German Excel:
- **Totals:** `str(invoice.total)` writes decimal points, like `12.50`. German Excel may read that as text or a date rather than a number.
- **Special characters:** the file is UTF-8 without a BOM, a marker Excel uses to recognise UTF-8. Without it, Excel usually garbles umlauts in customer names.

Should I push the branch and create the MR?