I reverted `b6115e4` ("worker: retry failed exports") on `main` as commit `6011d49`, keeping git's default message:

```
Revert "worker: retry failed exports"

This reverts commit b6115e4d48462256b803db9a5ed357fa1455f05c.
```

That commit was what created `worker/export.py` and `worker/test_export.py`, so reverting it deletes both files outright. If any other code imports from `worker/export.py`, it will now break. I didn't run the tests. Nothing was pushed.