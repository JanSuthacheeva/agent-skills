I committed the backoff change as `fe520e8` on `feature/export-backoff`:

```
worker: back off exponentially between export retries

A fixed 1s delay retried too aggressively against a struggling
endpoint. Delays now double from 0.5s, and the default retry count
goes from 3 to 5 to cover longer outages.
```

The commit contains `worker/export.py` and `worker/test_export.py`. I didn't run the tests before committing.

I left out `debug_dump.txt` and `notes.md` because they look like scratch files. They're still untracked. The branch name has no ticket ID, so there's no `Refs:` trailer.