I committed the pagination work as `db8670a api: invoices: paginate invoice list endpoint`. It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the test.

I left `worker/export.py` out on purpose. Its only change is an unrelated note ("WIP: try jitter here, not done yet"), so it's still uncommitted in your working tree.

Your instructions say to use the `/commit` skill, but it isn't available in this session, so I made the commit by hand in the same `scope: description` style as your recent commits.