I committed the staged change to `api/auth.py` as `3e75bf0`: "auth: Allow 60s clock skew leeway in token expiry check".

The change adds a 60-second leeway to the token expiry check. This stops mobile clients with drifting clocks from having fresh tokens rejected as expired.

I didn't run any tests.