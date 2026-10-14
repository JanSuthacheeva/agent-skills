I committed the staged change to `api/auth.py` as `437ba23` on `HGAI-3187-token-clock-skew`:

`api: auth: allow 60s clock skew leeway in token expiry check`

The body explains why: mobile clients drift by up to a minute, so fresh tokens were being rejected as expired. It also has a `Refs: HGAI-3187` line taken from the branch name.

There is no `/commit` skill in this session, so I ran `git commit` directly. I matched the `api: auth:` scope style from the recent history.