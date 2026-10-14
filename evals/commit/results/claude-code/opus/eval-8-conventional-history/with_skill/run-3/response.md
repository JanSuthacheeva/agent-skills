I committed the staged change to `worker/export.py` as `3c5ce39`:

```
worker: add jitter to export retry delay

A fixed one-second delay makes concurrent failed exports retry in
lockstep and hit the client again at the same moment.
```

The repo's history uses conventional prefixes like `fix(worker):`, but the commit skill forbids type prefixes, so I used `worker:` instead. The branch is `main` and has no ticket ID, so there's no `Refs:` trailer. Nothing else was staged or changed.