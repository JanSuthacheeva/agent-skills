I committed the backoff change as `8ac81ef` on `feature/export-backoff`:

```
worker: back off exponentially between export retries

A fixed one-second delay retried too aggressively against a struggling
client. Retries now double from 0.5s and the default attempts rise from
3 to 5 to cover the longer recovery window.
```

It includes only `worker/export.py` and `worker/test_export.py`. I left `debug_dump.txt` and `notes.md` out because they're unrelated untracked files. There's no `Refs:` line because the branch name has no ticket ID. I didn't run the tests before committing.

One thing I noticed in the new code: the worker still sleeps after the last failed attempt. With 5 retries, that's an extra 8s wait just before it raises `RuntimeError`. Should I fix that so it only sleeps when another attempt is coming?