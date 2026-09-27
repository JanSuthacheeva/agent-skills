I committed the staged change to `api/auth.py` as `bb0d8ef` on `HGAI-3187-token-clock-skew`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.

Refs: HGAI-3187
```

Nothing else was modified or staged, and nothing was pushed.