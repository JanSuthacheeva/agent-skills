I committed the staged change as `53fd89d`:

```
auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so their fresh tokens were rejected as expired.
```

Your instructions say to use the `/commit` skill, but there isn't one installed here, so I wrote the commit by hand. I used the `<scope>: <description>` format even though the earlier commits in this repo don't have scopes.