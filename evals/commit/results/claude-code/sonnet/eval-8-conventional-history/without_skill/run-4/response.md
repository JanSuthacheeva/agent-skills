I committed the staged change to `worker/export.py` as `ea9d6b1`: `fix(worker): add jitter to export retry backoff`.

The change adds a random 0-1s of jitter to the sleep between export retries. I didn't run any tests.

There is no `/commit` skill in this session, so I ran `git commit` directly. I matched the scope style of the existing history.