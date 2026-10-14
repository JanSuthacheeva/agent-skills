I committed the staged change to `worker/export.py` as af13977 on `main`:

```
worker: add jitter to export retry delay

Fixed 1s sleeps made concurrent exports retry in lockstep against
the same client.
```

I used no type prefix, even though the log uses `feat(...)` and `fix(...)`, because the skill's rules say not to. The branch name has no ticket ID, so there is no `Refs:` trailer. Nothing else was staged or left unstaged.