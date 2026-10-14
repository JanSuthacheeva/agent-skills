I committed the staged change to `api/auth.py` as `d3c4389`:

```
api: auth: allow 60s clock skew in token expiry check

Mobile clients drift by up to a minute, causing freshly issued tokens
to be rejected as expired.

Refs: HGAI-3187
```

The `/commit` skill your instructions ask for isn't installed in this session, so I wrote the message myself. It follows the repo's existing `api: auth:` scope style, and I took the ticket reference from the branch name.