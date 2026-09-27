I committed the backoff change and its test as `dfc31f3`:

```
worker: back off exponentially between export retries

A fixed one-second sleep hammered the client during longer outages.
Retries now double from 0.5s and go up to 5 attempts.
```

The branch name has no ticket ID, so there's no `Refs:` line. I left `debug_dump.txt` and `notes.md` out because they look like scratch files. They're still untracked. I didn't run the tests before committing.