I committed the exponential backoff change as `5d69fad` with the message "worker: use exponential backoff for export retries". There's no `/commit` skill available in this session, so I ran the git commands directly.

The commit contains `worker/export.py` and `worker/test_export.py`. I didn't run the tests.

I left `debug_dump.txt` and `notes.md` out because they're untracked and unrelated to this change. They're still untracked.