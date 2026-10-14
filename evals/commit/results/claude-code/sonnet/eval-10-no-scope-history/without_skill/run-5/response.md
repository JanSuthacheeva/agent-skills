I committed the staged change to `api/auth.py` as `084b3d1`: `auth: Allow 60s clock skew leeway in token expiry check`.

The change adds a `CLOCK_SKEW_LEEWAY` of 60 seconds to the token expiry check in `token_valid`. This stops fresh tokens from mobile clients with drifting clocks being rejected as expired. I didn't run any tests.