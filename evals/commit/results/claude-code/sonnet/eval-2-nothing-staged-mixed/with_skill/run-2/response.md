I committed the exponential backoff as f7dcb31 on `feature/export-backoff`. I didn't run the tests.

```
worker: back off exponentially when retrying failed exports

A fixed 1s sleep hammered the export endpoint while it was
struggling. Delay now doubles per attempt from 0.5s, and the default
retry count rises from 3 to 5 to cover the longer window.
```

- **Included:** `worker/export.py` and `worker/test_export.py`.
- **Left out:** `debug_dump.txt` and `notes.md`. Both are untracked and unrelated to the backoff work.
- **Refs trailer:** I didn't add one, because the branch name has no ticket ID.
- **Body:** I wrote the "hammered the endpoint" rationale myself, since the diff doesn't say why you changed it. Reword it if the real reason was different.