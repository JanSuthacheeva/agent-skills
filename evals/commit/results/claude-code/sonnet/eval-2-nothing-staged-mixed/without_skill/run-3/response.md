I committed the exponential backoff as `ca24965` with the message `worker: add exponential backoff to export retries`.

It includes `worker/export.py` and `worker/test_export.py`. I didn't run the tests before committing.

There is no `/commit` skill in this session, so I ran plain `git commit` instead.

I left `debug_dump.txt` and `notes.md` untracked because they aren't part of this change.