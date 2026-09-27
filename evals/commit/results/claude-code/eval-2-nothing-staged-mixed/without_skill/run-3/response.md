I committed the backoff change on `feature/export-backoff` as `b0ed0a6 worker: use exponential backoff for export retries`. It includes `worker/export.py` and the new test in `worker/test_export.py`. I didn't run the tests before committing.

Two things in the change you might not expect: the default retry count went from 3 to 5, and the delay now starts at 0.5s and doubles each retry.

I left `debug_dump.txt` and `notes.md` out because they look like scratch files. They're still untracked. Nothing was pushed.