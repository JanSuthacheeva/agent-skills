I committed the backoff change as `59a1642` on `feature/export-backoff`. I didn't run the tests first.

```
worker: back off exponentially between export retries

A fixed one-second sleep kept hammering the client during longer
outages. Doubling the delay from 0.5s and allowing five attempts
gives the remote side time to recover.
```

The commit has `worker/export.py` and `worker/test_export.py`. I left out two untracked files that aren't part of this work: `debug_dump.txt` and `notes.md`. The branch name has no ticket ID, so the message has no `Refs:` line.