I reverted the export retry commit `c9e1b4c` as `4c6a56a` on `main`, using git's default revert message. Nothing was pushed, and I didn't run any tests.

```
Revert "worker: retry failed exports"

This reverts commit c9e1b4ced4b460fec482465d2659aa5c45cde059.
```

- **The revert removes the whole export function, not just the retry.** That commit created `worker/export.py` and `worker/test_export.py`, so both files are now gone. No other Python code calls it, so nothing else breaks.
- **Likely cause of the duplicates:** the retry loop resent the export whenever it hit a `ConnectionError`. If the first send actually reached the server but the response was lost, the retry sent the same invoice again. Nothing let the server recognise the repeat, such as an idempotency key (a unique ID sent with each export). If you bring retries back, the server needs a way to ignore repeats of the same invoice.