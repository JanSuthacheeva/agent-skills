**Title**

```
SHOP-217 Invoices: Export as CSV
```

**Description**

```
Accounting had no way to get invoices out of the shop as a file. This adds a CSV export of invoices, served as a download from the API.

- Rows are generated one at a time and written straight to the response (batches of 500), so exporting 50,000 invoices does not hold them all in memory.
- The separator is a semicolon, because the accounting team opens the file in German Excel, which reads commas as decimal marks.

Refs: SHOP-217
```

Things I noticed but left out of the description, since the commits don't give a reason for them:
- `api/export.py` only defines `export_invoices`. The diff registers no route for it, so the endpoint may not be reachable yet. Is that wired up elsewhere or in a follow-up?
- `total` is written with `str()`, so it uses a dot as the decimal mark. That may clash with the German Excel reasoning behind the semicolon.

`glab` is available and no MR is open for this branch. I haven't pushed or created anything. Tell me to create it when you want that, and I'll push and open the MR.