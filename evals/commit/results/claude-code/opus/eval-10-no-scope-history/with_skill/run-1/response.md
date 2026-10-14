I committed the staged change to `api/auth.py` on `main` as `d05bec1`:

```
api: auth: allow 60s clock skew when checking token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired.
```

None of the earlier commits use scopes, so I named this one after the file's path. I didn't add a `Refs:` trailer because the branch name has no ticket ID.