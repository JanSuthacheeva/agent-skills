I committed the staged change to `worker/export.py` as `510a832` on `main`:

```
worker: add jitter to export retry delay

A fixed 1s sleep makes concurrent failed exports retry in lockstep,
hitting the client again all at the same moment.
```

The change adds a random extra delay of up to 1 second on top of the fixed 1-second wait between retries. The reason in the body is my guess at why, since nothing in the diff says so; I can amend it if the reason was different.

I left out the `feat`/`fix` prefix even though the history uses it, because this format drops it. There's no `Refs:` line because the branch `main` has no ticket ID.