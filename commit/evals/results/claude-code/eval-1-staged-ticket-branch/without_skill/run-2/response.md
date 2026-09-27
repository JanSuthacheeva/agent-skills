I committed the staged change to `api/auth.py` as `1edb684` on `HGAI-3187-token-clock-skew`:

```
api: auth: allow 60s clock skew on token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired. Accept tokens up to 60 seconds past exp.

Refs: HGAI-3187
```

The `/commit` skill your instructions ask for isn't installed in this session, so I wrote the message by hand. It follows the repo's existing `api: auth:` scope style and references the ticket from the branch name. Nothing was pushed.