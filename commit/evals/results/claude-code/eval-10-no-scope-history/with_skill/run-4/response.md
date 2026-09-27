I committed the staged change to `api/auth.py` on `main` as `4f94223`:

```
api: auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were
rejected as expired.
```

There were no other changes in the working tree, and the branch name has no ticket ID, so there's no `Refs:` trailer.