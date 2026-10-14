I committed the backoff change as `2567f08` on `feature/export-backoff`: `worker: use exponential backoff for export retries`.

- **Included:** `worker/export.py` and `worker/test_export.py`. The wait between retries now starts at 0.5s and doubles each attempt, and the default number of retries goes up from 3 to 5. There's also a new test that checks the waits are 0.5s, 1s and 2s.
- **Left out:** `debug_dump.txt` and `notes.md`. They're unrelated untracked files, so they're still uncommitted.

I didn't run the tests before committing. Also, your instructions say to use the `/commit` skill, but it isn't installed in this session, so I made the commit with git directly.