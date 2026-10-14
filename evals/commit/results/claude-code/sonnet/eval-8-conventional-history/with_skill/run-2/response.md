I committed the staged change to `worker/export.py` as d354e1d on `main`:

```
worker: add jitter to export retry delay

Fixed one-second sleeps made concurrent workers retry in lockstep
after a connection failure.
```

I used the `worker` scope from the log and left off the `fix(...)` type prefix, as the skill requires. The branch name has no ticket ID, so there is no `Refs` trailer. Nothing else was left uncommitted.