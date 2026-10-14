I reverted the export retry commit (`a3c9413`) on `main`. The new commit is `2f3e1cc` and uses git's default revert message:

```
Revert "worker: retry failed exports"

This reverts commit a3c94130c1e32105a25ebbab91621e6100248493.
```

**This removed more than the retry logic.** That commit is where `worker/export.py` and `worker/test_export.py` were first added, so the revert deleted both files. If anything else uses `worker/export.py`, it's now gone too, and you may want to restore it without the retry part.

I didn't reproduce the duplicate exports first, so I haven't confirmed that the retry was the cause. Nothing has been pushed.