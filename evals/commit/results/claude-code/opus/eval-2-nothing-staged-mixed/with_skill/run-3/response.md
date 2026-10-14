I committed the backoff change as `e77d974`:

```
worker: back off exponentially between export retries

A fixed one-second delay hammered the client during longer outages.
Retries now double from 0.5s, and the default attempts go from 3 to 5
to cover the longer window.
```

I guessed the reason in the body from the diff. If the real motivation was different, I can amend it.

The commit has `worker/export.py` and `worker/test_export.py`. I didn't run the tests before committing.

I left out two untracked files that look like scratch files: `debug_dump.txt` and `notes.md`.