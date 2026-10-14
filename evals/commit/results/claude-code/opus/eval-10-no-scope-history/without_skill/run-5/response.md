I committed the staged change as `aa6b203`:

```
auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, causing fresh tokens to be rejected as expired.
```

It covers only `api/auth.py`, which adds a 60-second leeway to the token expiry check.

Your instructions say to use the `/commit` skill, but this session doesn't have it, so I wrote the message by hand. I used the `<scope>: <description>` format, even though earlier commits in this repo don't have scopes.