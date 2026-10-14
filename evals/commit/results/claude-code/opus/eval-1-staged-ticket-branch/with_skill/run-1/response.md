I committed the staged change to `api/auth.py` as `7950a99` on `HGAI-3187-token-clock-skew`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.

Refs: HGAI-3187
```

Nothing was pushed.