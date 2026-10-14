I committed the export backoff as c5fc1e7 on `feature/export-backoff`. I didn't run the tests.

```
worker: back off exponentially between export retries

A fixed 1s sleep hammered the client during outages. Delay now
doubles from a 0.5s base, and the retry limit rises from 3 to 5.
```

It includes `worker/export.py` and `worker/test_export.py`. The branch name has no ticket ID, so there is no `Refs:` trailer.

The "hammered the client during outages" line in the body is my guess at the motivation. Amend it if the real reason differs.

I left out two untracked files that aren't part of this work:
- `debug_dump.txt`: a debug dump of client payloads.
- `notes.md`: a TODO to ask ops about the retry ceiling.