I reverted the export retry commit (`d833b9a`) on `main` as `b5883bb`, using git's default revert message:

```
Revert "worker: retry failed exports"

This reverts commit d833b9a05c03bc85c1c9661ab117a488c113d691.
```

That commit is what created `worker/export.py` and `worker/test_export.py`, so the revert deletes both files completely. If export code had been added in those files after that commit, it would be gone too. Nothing like that existed: neither file changed in any later commit.

I didn't reproduce the duplicate exports, so I can't confirm the revert stops them. I haven't pushed anything.