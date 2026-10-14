I reverted the export retry commit (308f9cf) as 6de0948 on `main`, keeping git's default message:

```
Revert "worker: retry failed exports"

This reverts commit 308f9cf265ac12bf757fe35bd7faf854f9a44ce9.
```

The revert removed `worker/export.py` and `worker/test_export.py`, since that commit had added both files. I didn't run any tests, and I haven't pushed.