I committed the staged change to `worker/export.py` on `main`:

```
worker: add jitter to export retry delay

A fixed one-second delay makes failed exports retry in lockstep,
hitting the client again all at once.
```

The reason in the body is my guess, since the diff only shows the retry delay changing from 1 second to 1 to 2 seconds. Change it if the real reason was different.

The message has no `feat`/`fix` prefix, as the commit skill requires, even though earlier commits use them. There's no `Refs:` line because the branch name has no ticket ID. Nothing else was staged or changed.