I committed the staged change in `api/auth.py` as `e84005e`:

```
api: allow 60s clock skew leeway in token expiry check
```

The commit body explains why: mobile clients' clocks can be up to a minute off, so their fresh tokens were being rejected as expired.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I wrote the commit by hand in the `<scope>: <description>` format. Earlier commits in this repo don't use scopes, so I picked `api` from the directory name.