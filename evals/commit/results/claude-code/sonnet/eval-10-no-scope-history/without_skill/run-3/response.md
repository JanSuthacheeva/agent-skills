I committed the staged change to `api/auth.py` as a2c8418: `auth: Allow 60s clock skew leeway in token expiry check`.

The token expiry check now accepts tokens up to 60 seconds past their expiry. This stops mobile clients with drifting clocks from having fresh tokens rejected as expired. I didn't run any tests.