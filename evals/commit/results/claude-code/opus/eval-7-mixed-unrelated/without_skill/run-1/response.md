I committed the pagination work as `ec8a763 api: paginate invoice list endpoint`. It includes the changes to `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the test: my attempt to run it was blocked at a permission prompt.

I left `worker/export.py` out on purpose. Its only change is a comment marked "WIP: try jitter here, not done yet", which isn't related to pagination, so it's still uncommitted in your working tree.

The `/commit` skill your instructions call for isn't available in this session, so I made the commit with git directly.