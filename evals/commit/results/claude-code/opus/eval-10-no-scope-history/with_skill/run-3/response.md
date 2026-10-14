I committed the staged change to `api/auth.py` as `8a87fda`:

```
api: auth: allow 60s clock skew when checking token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

None of the earlier commit messages use a scope, so I took `api: auth` from the file path. That was the only change in the working tree. Nothing was pushed and the branch has no ticket ID, so there's no `Refs:` line.