I committed the staged change to `api/auth.py` as `0dea5fd` on `HGAI-3187-token-clock-skew`. Nothing was pushed.

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired.

Refs: HGAI-3187
```