Title: `SHOP-217 Invoices: Export as CSV`

```
Accounting needs invoices in a spreadsheet. This adds a CSV export of invoices, served as a download from the API.

- Rows are generated one at a time and written straight to the response, so exporting 50,000 invoices does not hold them all in memory.
- The separator is a semicolon, because the accounting team opens the file in German Excel, which reads commas as decimal marks.

Refs: SHOP-217
```

Notes:
- No MR exists yet for this branch, and the working tree is clean.
- The "Accounting needs invoices in a spreadsheet" framing comes from the commit message about the accounting team. The ticket itself only gives the title, so correct me if the goal was different.
- I have not pushed or created the MR. Tell me to push and create it when you want that.