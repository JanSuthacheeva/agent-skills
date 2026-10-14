I committed the staged change to `api/auth.py` as 985aa34:

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The branch is `main`, so there is no `Refs:` trailer. Nothing else was staged or modified.