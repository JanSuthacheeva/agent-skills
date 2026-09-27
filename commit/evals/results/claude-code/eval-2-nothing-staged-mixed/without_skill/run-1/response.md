I committed the backoff change on `feature/export-backoff` as `9f8af52 worker: back off exponentially on export retries`. I didn't run the tests before committing.

The commit contains:
- `worker/export.py`: the export worker now retries 5 times instead of 3, waiting 0.5s, 1s, 2s and so on between tries instead of a flat 1s.
- `worker/test_export.py`: a new test that checks those wait times.

I didn't commit two untracked files, `debug_dump.txt` and `notes.md`, because they look like scratch files. Nothing was pushed.