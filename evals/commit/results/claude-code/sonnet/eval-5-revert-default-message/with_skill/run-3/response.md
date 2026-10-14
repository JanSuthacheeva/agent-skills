I reverted the export retry commit (308f9cf, "worker: retry failed exports") as d5e9592 on `main`. I didn't run any tests.

The commit uses git's default message, as the commit skill requires for reverts:

```
Revert "worker: retry failed exports"

This reverts commit 308f9cf265ac12bf757fe35bd7faf854f9a44ce9.
```

The revert deleted `worker/export.py` and `worker/test_export.py`. Both files were added by the original commit, so the export worker no longer exists on `main`. If you expected the worker to remain without the retry logic, that needs a follow-up. I didn't push anything.