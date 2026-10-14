I committed the pagination change as `e907598` with the message "api: paginate invoice list endpoint". It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the tests before committing.

I left `worker/export.py` out. Its only change is an unfinished "WIP: try jitter" comment, and it's still modified in your working tree.

There's no `/commit` skill in this session, so I committed manually and followed the repo's `scope: description` message style.