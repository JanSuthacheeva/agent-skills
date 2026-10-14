Title and description (nothing pushed or created yet):

**Title**

```
SHOP-217 Invoices: Export as CSV
```

**Description**

```
Accounting had no way to get invoices out of the system in bulk. This adds a CSV export of invoices, served as a download from the API.

- Rows are generated one at a time and written straight to the response (batches of 500), so exporting 50,000 invoices does not hold them all in memory.
- The separator is a semicolon, because the accounting team opens the file in German Excel, which reads commas as decimal marks.

Refs: SHOP-217
```

The branch is small (3 files, 23 lines), so I left out a review guide. There are no deploy steps: no new config, dependencies or migrations. No MR exists yet for this branch, and the working tree is clean.

Tell me when you want me to push the branch and create the MR.