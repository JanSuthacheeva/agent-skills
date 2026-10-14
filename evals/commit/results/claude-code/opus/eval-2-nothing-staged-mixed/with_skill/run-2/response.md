I committed the backoff change on `feature/export-backoff` as `8ae9924`:

```
worker: back off exponentially between export retries

A fixed one-second delay retried too aggressively while the export
target was recovering. Retries also go up from 3 to 5 so the longer
waits still fit within a reasonable total window.
```

The commit holds `worker/export.py` and `worker/test_export.py`. The waits between retries now start at 0.5s and double each time, and there are 5 retries instead of 3. I didn't run the tests.

I wrote the reasons in the message body myself from the diff, not from anything you told me. If they don't match why you made the change, I can amend the message.

I left two untracked files out of the commit:
- `debug_dump.txt`
- `notes.md`, which holds a TODO: "ask ops about retry ceiling". That question is still open now that retries go up to 5.

No branch ID matched the ticket pattern, so the commit has no `Refs:` line.