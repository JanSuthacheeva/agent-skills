I committed the staged change in `api/auth.py` as `578daa0`:

```
auth: allow 60s clock skew leeway in token expiry check

Mobile clients drift by up to a minute, causing fresh tokens to be
rejected as expired.
```

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I wrote the message myself in the `<scope>: <description>` format.