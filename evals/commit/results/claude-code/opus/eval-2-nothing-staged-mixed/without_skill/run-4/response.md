I committed the backoff change as `6a95e20 worker: use exponential backoff for export retries`. I didn't run the tests before committing.

The commit includes `worker/export.py` and the new test in `worker/test_export.py`. Retries now default to 5 instead of 3. Each retry waits twice as long as the one before, starting at 0.5s.

I left `debug_dump.txt` and `notes.md` out because they don't look related to this change. They're still untracked.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I wrote the message myself in the repo's `scope: description` style.