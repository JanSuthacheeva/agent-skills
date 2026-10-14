I committed the staged change to `api/auth.py` as `535fe34` on `HGAI-3187-token-clock-skew`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile client clocks drift by up to a minute, so freshly issued tokens
were rejected as expired.

Refs: HGAI-3187
```

Nothing has been pushed.