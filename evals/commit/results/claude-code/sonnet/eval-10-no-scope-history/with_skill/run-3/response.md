I committed the staged change to `api/auth.py` on `main` as `decf565`. Nothing was pushed.

```
api: auth: allow 60s clock skew when validating token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

The branch name has no ticket ID, so there is no `Refs:` trailer. There were no unstaged or untracked files to leave out.