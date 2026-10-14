I reverted `e62110a` ("worker: retry failed exports") as `59cf0de`, with the message "worker: revert retry failed exports". I didn't run any tests.

The revert deleted `worker/export.py` and `worker/test_export.py` entirely, because that commit created both files. If anything else relies on them, it will break. Say so if you wanted only the retry logic removed and the export code kept.

I used a plain `git commit` because the `/commit` skill isn't available in this session.