I committed the backoff change as `a04a239` with the message "worker: add exponential backoff to export retries". I didn't run the tests.

It covers `worker/export.py` and `worker/test_export.py`. The default retries go from 3 to 5, and the sleep between attempts is now `base_delay * 2 ** attempt` (0.5s base) instead of a fixed 1s.

I left `debug_dump.txt` and `notes.md` uncommitted since they aren't part of this change. Also, there is no `/commit` skill in this session, so I committed directly with git.