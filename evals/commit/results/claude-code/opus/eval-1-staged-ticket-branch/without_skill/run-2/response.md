I committed the staged change as `8af1e67`:

```
api: auth: allow clock skew leeway on token expiry

Mobile clients drift by up to a minute, causing freshly issued tokens
to be rejected as expired. Accept tokens up to 60 seconds past exp.

Refs: HGAI-3187
```

The ticket number HGAI-3187 comes from the branch name. Your instructions say to use the `/commit` skill, but it isn't available in this session, so I wrote the message myself. It follows the repo's existing `api: auth:` scope style.