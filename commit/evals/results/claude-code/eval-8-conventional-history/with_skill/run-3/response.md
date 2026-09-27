I committed the staged change to `worker/export.py` as `7a43f29`:

```
worker: add jitter to export retry delay

A fixed one-second delay makes concurrent exports that fail together
retry in lockstep. Random jitter spreads the retries out.
```

Your recent commits use `feat(...)`/`fix(...)` prefixes, but I left the type prefix off because the commit skill requires plain `<scope>: <description>`. The `worker` scope matches your earlier worker commit. There's no `Refs:` trailer because the branch is `main`, which has no ticket ID.