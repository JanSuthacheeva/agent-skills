I reverted the export retry commit `a3c9413` ("worker: retry failed exports") as `ed70f70`, using git's default revert message:

```
Revert "worker: retry failed exports"

This reverts commit a3c94130c1e32105a25ebbab91621e6100248493.
```

The original commit only added `worker/export.py` and `worker/test_export.py`, so the revert deletes both files. I didn't reproduce the duplicate exports or run tests after the revert. Nothing was pushed.