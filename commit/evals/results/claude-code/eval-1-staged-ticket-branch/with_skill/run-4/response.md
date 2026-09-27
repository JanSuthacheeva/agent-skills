I committed the staged change to `api/auth.py` as `ea9b81d`:

```
api: auth: allow 60s clock skew on token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired.

Refs: HGAI-3187
```