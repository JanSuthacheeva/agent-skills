I committed the staged change to `api/auth.py` as `ce8d3f9`: "auth: Allow 60s clock skew leeway in token expiry check".

The change adds a 60-second leeway to the token expiry check. The commit body explains why: mobile clients drift by up to a minute, so fresh tokens were being rejected as expired.

No `/commit` skill is available in this session, so I ran `git commit` directly. I used the scoped format (`auth: ...`) even though the earlier commits in the history don't use scopes.