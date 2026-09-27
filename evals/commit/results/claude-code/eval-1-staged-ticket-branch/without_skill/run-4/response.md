I committed the staged change to `api/auth.py` as `ede3ed8`:

```
api: auth: allow clock skew leeway on token expiry

Mobile clients drift by up to a minute, so freshly issued tokens were
rejected as expired. Accept tokens up to 60s past their exp.

Refs: HGAI-3187
```

The `/commit` skill your instructions ask for isn't installed in this session, so I wrote the message by hand. The scope follows the repo's existing `api: auth:` style, and the ticket number comes from the branch name.