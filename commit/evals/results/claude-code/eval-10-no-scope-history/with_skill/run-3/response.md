I committed the staged change to `api/auth.py` as `890a206`:

```
api: auth: allow 60s clock skew when checking token expiry

Mobile clients drift by up to a minute, so their freshly issued tokens
were rejected as expired.
```

The existing commit log doesn't use scopes, so I named the scope after the path the change touches. There's no `Refs:` trailer because you're on `main`, which has no ticket ID.