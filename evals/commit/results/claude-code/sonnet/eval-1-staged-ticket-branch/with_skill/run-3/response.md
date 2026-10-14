I committed the staged change to `api/auth.py` as 5965268 on `HGAI-3187-token-clock-skew`. I didn't push.

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens
were rejected as expired.

Refs: HGAI-3187
```