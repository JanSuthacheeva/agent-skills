I committed the staged change to `api/auth.py` as e264148 on `main`. I didn't run any tests.

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The branch name has no ticket ID, so there is no `Refs:` trailer.