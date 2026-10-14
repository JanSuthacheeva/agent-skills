Committed as 385aaf0 on `main`:

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The branch name has no ticket ID, so there is no `Refs` trailer.