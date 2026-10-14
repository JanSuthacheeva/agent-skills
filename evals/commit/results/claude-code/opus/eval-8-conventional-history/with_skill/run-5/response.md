I committed the staged change to `worker/export.py` on `main` as `e9a3e39`:

```
worker: add jitter to export retry delay

A fixed one-second delay makes concurrent exports retry in lockstep
and hit the client again at the same moment.
```

I wrote the body's reason myself from the diff - nothing in the change states it. If you had a different reason for the jitter, the message should be amended.

The subject has no `fix`/`feat` prefix even though your log uses them, because the commit skill's Scoped Commits format drops type prefixes. Nothing else was in the working tree, so no other changes were left out.