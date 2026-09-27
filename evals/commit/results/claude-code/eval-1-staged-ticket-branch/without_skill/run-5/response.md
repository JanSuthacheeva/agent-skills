I committed the staged change to `api/auth.py` on `HGAI-3187-token-clock-skew`:

```
3026628 api: auth: allow 60s clock skew leeway on token expiry
```

The commit message also explains why: mobile clients' clocks can be up to a minute off, so newly issued tokens were being rejected as expired.

- **No `/commit` skill:** your instructions say to use it, but it isn't installed in this session. I used the `git-conventions` skill instead. That skill asks for the `feat(scope):` format, but I followed this session's `<scope>: <description>` format, which your earlier commits (like `api: auth: ...`) also use.
- **Ticket ID:** your earlier commit messages don't include ticket IDs, so I left HGAI-3187 out of the message. It's still in the branch name.

The commit is local only. Tell me to push if you want it on the remote.