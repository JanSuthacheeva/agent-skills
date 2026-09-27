I committed the staged change to `worker/export.py` as `e13db95` on `main`:

```
worker: add jitter to export retry delay

A fixed one-second sleep makes concurrent failed exports retry in
lockstep and hit the client again at the same moment. A random
jitter spreads the retries out.
```

Your log uses type prefixes like `fix(worker):`, but I left the prefix off and kept `worker` as the scope. There's no `Refs:` line because the branch name `main` has no ticket ID. Nothing else was changed or staged.