I committed the staged change as `39284a4` on `HGAI-3187-token-clock-skew`:

```
api: auth: allow clock skew leeway on token expiry

Mobile clients drift by up to a minute, so freshly issued tokens were
rejected as expired. Accept tokens up to 60 seconds past exp.

Refs: HGAI-3187
```

There was no `/commit` skill available, so I followed the repo's existing `api: auth:` scope style and added the ticket from the branch name as a `Refs:` line. I didn't push.