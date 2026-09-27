I committed the staged change to `api/auth.py` as `bfa86cf` on `main`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

`main` doesn't contain a ticket ID, so there's no `Refs:` trailer. Nothing else was left unstaged.