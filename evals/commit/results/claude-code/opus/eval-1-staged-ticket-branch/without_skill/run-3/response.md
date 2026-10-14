I committed the staged change in `api/auth.py` as `80540bc`:

```
api: auth: allow 60s clock skew on token expiry

Mobile clients drift by up to a minute, so freshly issued tokens were
rejected as expired. Accept tokens up to 60 seconds past exp.

Refs: HGAI-3187
```

I took the ticket number from the branch name and added it as a `Refs:` trailer, since none of the earlier commits mention tickets. Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I followed the scoped-commit style from the git history instead.