I reverted the export retry commit (399ae28). The revert is committed as `ec33644` on `main` with git's standard message:

```
Revert "worker: retry failed exports"

This reverts commit 399ae28ce037d3a82e6da0163bf482d189aca934.
```

That commit is what created `worker/export.py` and `worker/test_export.py`, so the revert deletes both files completely, not just the retry logic. Nothing else in the repo was touched, and nothing was pushed.

I haven't reproduced the duplicate exports or run any tests, so it isn't confirmed yet that this stops them.