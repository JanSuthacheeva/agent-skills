I committed the staged change in `api/auth.py` as `716e1ed`:

```
api: auth: allow clock skew leeway on token expiry

Mobile clients drift by up to a minute, causing freshly issued tokens
to be rejected as expired. Accept tokens within 60s past expiry.

Refs: HGAI-3187
```

Your instructions say to commit with the `/commit` skill, but it isn't available in this session, so I wrote the message myself. It follows the `api: auth:` scope used in earlier commits, and I took the ticket number HGAI-3187 from the branch name.