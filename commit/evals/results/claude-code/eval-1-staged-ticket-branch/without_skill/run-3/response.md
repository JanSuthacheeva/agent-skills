I committed the staged change to `api/auth.py` as `48977aa` on `HGAI-3187-token-clock-skew`:

```
api: auth: allow 60s clock skew on token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired. Accept tokens up to 60 seconds past exp.

Refs: HGAI-3187
```

Your instructions say to use the `/commit` skill, but it isn't installed in this session. I wrote the message by hand instead, matching the scope style of your recent commits (`api: auth:`). The `Refs: HGAI-3187` line comes from the branch name. Your past commits don't use that trailer, so I can remove it if you don't want it.