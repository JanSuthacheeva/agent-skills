I committed the staged change to `api/auth.py` as `171ed6d`:

```
api: auth: allow 60s clock skew when checking token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired.
```

The earlier commits in the log don't use scopes, so I took `api: auth` from the file's path. There's no `Refs:` trailer because the branch is `main` and has no ticket ID.