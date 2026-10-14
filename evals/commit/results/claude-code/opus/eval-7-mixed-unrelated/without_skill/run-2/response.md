I committed the pagination work as `e233859 api: paginate invoice list endpoint`. It includes the `list_invoices` changes in `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the test.

I left out `worker/export.py`, which is still uncommitted. Its only change is an unrelated comment, `# WIP: try jitter here, not done yet`.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I committed with plain git instead.