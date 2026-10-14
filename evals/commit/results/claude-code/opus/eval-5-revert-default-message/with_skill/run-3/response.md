I reverted the export retry commit (d833b9a) on `main` as 361a19c, using git's default message:

```
Revert "worker: retry failed exports"

This reverts commit d833b9a05c03bc85c1c9661ab117a488c113d691.
```

That commit had created both `worker/export.py` and `worker/test_export.py`, so the revert deletes both files instead of just removing the retry logic. If anything else depends on `worker/export.py`, it will break. In that case, the better fix may be to restore the file and take out only the retry.

Nothing has been pushed.