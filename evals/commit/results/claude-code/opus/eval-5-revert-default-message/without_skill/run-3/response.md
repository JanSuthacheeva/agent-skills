I reverted `705d4fb` (worker: retry failed exports) as `386aa37 worker: revert export retries`. The commit message says the retries were causing duplicate exports.

That commit had created both `worker/export.py` and `worker/test_export.py`, so the revert deletes both files. No later commit had changed them, so it applied without conflicts. I haven't run any tests.

Your instructions say to use the `/commit` skill, but it isn't available in this session, so I wrote the commit by hand in the same `<scope>: <description>` format.