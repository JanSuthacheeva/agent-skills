I reverted `c401cfd` ("worker: retry failed exports") as `f771278` on `main`. I didn't run the tests, and I haven't checked that the duplicate exports are gone. I kept git's default revert message, as the commit skill says to for reverts:

```
Revert "worker: retry failed exports"

This reverts commit c401cfdd9aa5ca3d38f4f26f716c0aea56912658.
```

The revert deletes `worker/export.py` and `worker/test_export.py`, 14 lines in total. That means the retry commit had added both files, so the revert removes them entirely. Nothing was pushed.