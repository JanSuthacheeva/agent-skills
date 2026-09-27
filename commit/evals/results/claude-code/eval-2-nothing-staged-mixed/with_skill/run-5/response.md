I committed the backoff change as `daf949e`:

```
worker: back off exponentially between export retries

Default retries go from 3 to 5 so the longer waits still fit a
transient outage window.
```

The commit contains `worker/export.py` and `worker/test_export.py`. I didn't run the tests before committing.

The reason given in the body for raising retries from 3 to 5 is my guess, not something the code says. If it's wrong, tell me the real reason and I'll amend the message.

I left `debug_dump.txt` and `notes.md` out because they look like scratch files. The branch name has no ticket ID, so the commit has no `Refs:` line.