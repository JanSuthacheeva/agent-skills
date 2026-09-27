I reverted `7c21f5e` ("worker: retry failed exports") on `main`. The new commit is `57aceb5`, and it keeps git's default revert message:

```
Revert "worker: retry failed exports"

This reverts commit 7c21f5e898ae8db721579df41053306b50bcdafb.
```

That commit created both `worker/export.py` and `worker/test_export.py`, so the revert deletes both files completely (14 lines). Nothing else in the tree changed, and nothing was pushed.

I didn't reproduce the duplicate exports myself or run the tests after the revert. I took your diagnosis as given.