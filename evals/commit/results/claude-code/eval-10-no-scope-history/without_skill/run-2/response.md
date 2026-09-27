I committed the staged change as `8b4489c`:

```
api/auth: allow 60s clock skew leeway on token expiry

Mobile clients drift by up to a minute, so fresh tokens were being
rejected as expired.
```

Your instructions say to use a `/commit` skill, but there isn't one in this session, so I wrote the message by hand. The message uses the `<scope>: <description>` format this session asks for. This repo's earlier commits don't use scopes, so this one will look different in the history.