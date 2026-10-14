I committed the exponential backoff as `edb7b22` on `feature/export-backoff`: `worker: use exponential backoff for export retries`.

It covers `worker/export.py` and `worker/test_export.py`. I didn't run the tests.

I left `debug_dump.txt` and `notes.md` untracked because they aren't part of this change.

There was no `/commit` skill in the available list, so I ran the git commit directly. I used the scoped format `<scope>: <description>`.