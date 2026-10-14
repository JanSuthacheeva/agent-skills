I committed the pagination work as `81ddbd7` with the message `api: paginate invoice list endpoint`. It covers `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the tests.

I left `worker/export.py` out. Its only change is an unfinished "WIP: try jitter" comment, which has nothing to do with pagination. It's still modified in your working tree.

There's no `/commit` skill in this session, so I committed with plain git instead.