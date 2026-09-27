I reverted `c9e1b4c` on `main` as `3387520`, keeping git's default message:

```
Revert "worker: retry failed exports"

This reverts commit c9e1b4ced4b460fec482465d2659aa5c45cde059.
```

**Check this before you rely on it:** that commit created both `worker/export.py` and `worker/test_export.py`, so the revert deletes those two files outright rather than just removing the retry logic. If anything else uses `worker/export.py`, it will break. If you only want the retry behavior gone, I can undo this commit and remove just the retry code instead.

I haven't reproduced the duplicate exports or run any tests. Nothing was pushed.