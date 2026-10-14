I committed the staged change to `worker/export.py` on `main` as 51bd219:

```
worker: add jitter to export retry delay

Fixed one-second sleeps made concurrent workers retry in lockstep
against the same failing client.
```

I used the `worker` scope from the log and left off the `fix:` prefix. The branch name has no ticket ID, so there's no `Refs:` trailer. Nothing else was changed or left unstaged.