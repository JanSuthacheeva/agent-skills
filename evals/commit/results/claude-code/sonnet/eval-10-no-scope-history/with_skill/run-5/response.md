Committed as 7dffafe:

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The log had no scoped commits to reuse, so I used `api: auth:` from the file path.