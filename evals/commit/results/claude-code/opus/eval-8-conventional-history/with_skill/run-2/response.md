I committed the staged change to `worker/export.py` as `1c60318` on `main`:

```
worker: add jitter to export retry delay

A fixed one-second delay makes failed exports retry in lockstep and
hit the client again at the same moment.
```

The commit body's reason for the change is my inference from the diff; you didn't tell me why you made it. If that isn't the real reason, I can amend the message.

Your history uses `fix(worker):` style prefixes, but I used the plain `worker:` scope because the commit skill says not to use type prefixes. Nothing else was staged or modified.