I committed the pagination work as `fd9cb52 api: invoices: paginate invoice list endpoint`. It includes the changes to `api/invoices.py` and the new test file `api/test_invoices.py`. I didn't run the test before committing.

I left out `worker/export.py` because it isn't related: it's a half-finished retry jitter change (the comment says "WIP: try jitter here, not done yet"). It's still uncommitted in your working tree.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I wrote the commit by hand in the same scoped style as your recent commits.