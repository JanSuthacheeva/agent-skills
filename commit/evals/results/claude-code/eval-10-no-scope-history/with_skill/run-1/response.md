I committed the staged change to `api/auth.py` as `3037583` on `main`:

```
api: auth: allow 60s clock skew when checking token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The branch name has no ticket ID, so there's no `Refs:` trailer.