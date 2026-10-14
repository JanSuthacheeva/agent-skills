I committed the exponential backoff as `aa8e7ce` on `feature/export-backoff`:

```
worker: back off exponentially between export retries

A fixed one-second pause hammered the client during longer outages.
Doubling the delay from 0.5s and allowing five attempts gives the
remote side time to recover.
```

It covers `worker/export.py` and `worker/test_export.py`. I didn't run the tests before committing.

The reason given in the body is my guess from the diff, not something you told me. If the real motivation was different, I can amend the message.

I left two untracked files out of the commit:
- `debug_dump.txt`, a dump of client payloads
- `notes.md`, which has a TODO to ask ops about a retry ceiling

The branch name has no ticket ID, so the commit has no `Refs:` trailer.