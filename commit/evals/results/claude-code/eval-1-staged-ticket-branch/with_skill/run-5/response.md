I committed the staged change to `api/auth.py` as `dbca4b4`. Nothing else was in the working tree.

```
api: auth: allow 60s clock skew on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.

Refs: HGAI-3187
```