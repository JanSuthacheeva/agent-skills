I reverted the export retry commit (`6a19218`). The revert is committed as `92fd3f7 worker: revert "retry failed exports"`, and the message says the retry logic was causing duplicate exports.

That commit created `worker/export.py` and `worker/test_export.py` from scratch, so reverting it deletes both files completely. If export code from before the retry change should still be there, it needs to be restored separately.

I didn't reproduce the duplicate exports or run any tests. Your CLAUDE.md asks for the `/commit` skill, but it isn't available in this session, so I wrote the commit by hand in the same `scope: description` style.