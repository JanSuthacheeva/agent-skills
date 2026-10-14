Committed as c7a0d37:

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.

Refs: HGAI-3187
```