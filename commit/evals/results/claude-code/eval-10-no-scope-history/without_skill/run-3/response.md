I committed the staged change as `f572d7a`:

```
auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so freshly issued tokens were
rejected as expired.
```

Your global instructions say to use a `/commit` skill, but none is installed in this session, so I committed with plain git in the Scoped Commits format. The earlier commits in this repo don't use scopes, so I picked `auth` because the change is in `api/auth.py`. The working tree is clean.