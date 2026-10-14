I committed the staged change to `worker/export.py` as `ab3b28b` on `main`. I didn't run any tests.

```
worker: add jitter to export retry delay

Fixed one-second sleeps made concurrent exports retry in lockstep
after a shared connection failure.
```

I used the `worker` scope from the log and left off the `feat:`/`fix:` prefix the history uses. The branch name has no ticket ID, so there is no `Refs:` line.