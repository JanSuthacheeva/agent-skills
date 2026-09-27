I reverted the export retry commit (`cea1276`) as `20c35c7` on `main`, with git's default message:

```
Revert "worker: retry failed exports"

This reverts commit cea127609a29e9b8b742200c2bb973e0a30a4d12.
```

No later commits touched `worker/`, so it applied without conflicts. I didn't run the tests and nothing was pushed.

**The revert removes the export function entirely, not just the retry.** That commit created `worker/export.py` from scratch, so reverting it deleted `export()` and its test. If anything calls `worker.export`, it will now fail to import.

The likely cause of the duplicates: a `ConnectionError` can be raised after the server has already received and processed `client.send`, for example when the connection drops before the response comes back. The retry then sends the same export again. If you want to keep a retry, it needs something that stops the server processing the same export twice, such as a unique key per export that the server checks. I can restore `export()` without the retry, or add retry with that protection.