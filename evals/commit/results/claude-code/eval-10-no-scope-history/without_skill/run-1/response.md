I committed the change as `0eed66d` on `main`:

```
auth: allow 60s clock skew leeway in token expiry check

Mobile clients drift by up to a minute, so their fresh tokens were rejected as expired.
```

The commit contains only the staged change to `api/auth.py`. I didn't push it. There's no `/commit` skill in this session, so I committed directly and used the Scoped Commits format.