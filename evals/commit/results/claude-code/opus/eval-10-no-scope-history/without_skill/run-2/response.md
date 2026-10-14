I committed the staged change to `api/auth.py` as `bfbd346`:

```
auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were rejected as expired.
```

Your instructions say to use the `/commit` skill, but there isn't one in this session, so I wrote the message by hand. It uses the `<scope>: <description>` format, with `auth` as the scope. Earlier commits in this repo have no scope prefix.