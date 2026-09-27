I reverted `dd05929` ("worker: retry failed exports") with a new local commit on `main`:

```
8b7a111 worker: revert "retry failed exports"

This reverts commit dd05929ccfb31f2f0323957ff053a4a4824f4391.

The retry logic causes duplicate exports.
```

That original commit created `worker/export.py` and `worker/test_export.py` from scratch, so the revert deletes both files completely (14 lines). I didn't run the tests afterward. If other code imports from `worker/export.py`, it will now break.

I haven't pushed it. Say "push" if you want it on `origin/main`.