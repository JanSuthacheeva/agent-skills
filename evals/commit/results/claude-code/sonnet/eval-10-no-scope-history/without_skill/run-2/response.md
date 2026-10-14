I committed the staged change to `api/auth.py` as `1d18586`: `auth: Allow 60s clock skew leeway in token expiry check`.

The change adds a 60-second `CLOCK_SKEW_LEEWAY` to `token_valid`, so tokens from mobile clients with drifting clocks aren't rejected as expired. I didn't run any tests.