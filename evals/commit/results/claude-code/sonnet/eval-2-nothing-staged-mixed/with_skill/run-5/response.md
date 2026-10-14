I committed the exponential backoff as 4e6b470 on `feature/export-backoff`. I didn't run the tests.

```
worker: back off exponentially when retrying exports

A fixed 1s sleep hammered the export endpoint during outages.
Delay now doubles from 0.5s per attempt, and retries go from 3 to 5
so the total wait window is longer.
```

The commit contains `worker/export.py` and `worker/test_export.py`. The branch name has no ticket ID, so there is no `Refs:` trailer.

I left out `debug_dump.txt` and `notes.md`. Both are untracked and look unrelated to the backoff work.