I committed the backoff change as 31013d7 on `feature/export-backoff`. I didn't run the tests.

```
worker: back off exponentially between export retries

Fixed 1s sleeps hammered the client during outages. Delay now
doubles from a 0.5s base, and retries go from 3 to 5 to allow for
the longer waits.
```

The commit contains `worker/export.py` and `worker/test_export.py`. The body's "hammered the client during outages" reason is my inference from the diff, so check it matches your actual motivation.

I left `debug_dump.txt` and `notes.md` out because they're scratch files and not part of this work. Both are still untracked. The branch name has no ticket ID, so there is no `Refs:` trailer.