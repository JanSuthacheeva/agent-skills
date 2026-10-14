I committed the staged change to `api/auth.py` as `d37105f`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.

Refs: HGAI-3187
```

There were no other changes in the working tree.