I reverted `c1cef56` ("worker: retry failed exports") as commit `5fec396`. I kept git's default revert message, as the commit skill says to for reverts:

```
Revert "worker: retry failed exports"

This reverts commit c1cef5611c21426463c259bd186a45c471d2f095.
```

The revert applied cleanly. It deleted `worker/export.py` and `worker/test_export.py`, so those files were added entirely by the retry commit. I didn't run any tests, and nothing was pushed.