I committed the pagination work as `ee80d67 api: invoices: paginate invoice list endpoint`. The commit includes `api/invoices.py` and the new `api/test_invoices.py`.

- **Not committed:** `worker/export.py` only has a "WIP: try jitter here" comment, which isn't related to pagination. It's still uncommitted in your working tree.
- **Tests not run:** I tried to run the new test but the command needed approval, so it hasn't been run.
- **No `/commit` skill:** your instructions say to use it, but it isn't available in this session, so I made the commit with git directly.