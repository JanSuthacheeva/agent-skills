I committed the staged change to `api/auth.py` as `4273b34` on `main`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The scope comes from the file path, because earlier commits don't use scopes. There's no `Refs:` trailer because the branch name has no ticket ID.