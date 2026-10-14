I committed the staged change to `api/auth.py` on `main` as `e7eacde`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

Your earlier commits don't use scopes, so I took the scope from the folder and file name. I didn't add a `Refs:` line because the branch name has no ticket ID. That staged file was the only change, so nothing was left out.