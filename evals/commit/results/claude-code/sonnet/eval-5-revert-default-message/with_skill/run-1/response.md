I reverted the export retry commit (`d0f2b48`, "worker: retry failed exports") as `7050814`. It uses git's default revert message:

```
Revert "worker: retry failed exports"

This reverts commit d0f2b4801fc171e424b0c58c18ba5abd04a664ff.
```

The revert deleted `worker/export.py` and `worker/test_export.py`, since that commit had added both files. Nothing else was touched, and I didn't push. I didn't run any tests or try to reproduce the duplicate exports.