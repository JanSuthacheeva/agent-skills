I committed the staged change to `worker/export.py` as `dd20501` on `main`:

```
worker: add jitter to export retry backoff

A fixed one-second delay makes concurrent failed exports retry in
lockstep and hit the client again at the same moment.
```

- The reason in the message body is my guess from the diff, since I didn't have a stated reason for the change. If the real motivation was different, the message should be amended.
- I left out the `feat`/`fix` prefixes your earlier commits use, because the commit skill's format doesn't allow them.
- There was no `Refs:` line to add, because the branch name has no ticket ID.