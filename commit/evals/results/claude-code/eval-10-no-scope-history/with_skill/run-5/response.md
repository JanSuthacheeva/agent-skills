I committed the staged change to `api/auth.py` as `c5d9c29` on `main`:

```
api: auth: allow 60s clock skew when checking token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

There's no `Refs:` trailer because the branch name has no ticket ID. Nothing else was waiting to be committed.