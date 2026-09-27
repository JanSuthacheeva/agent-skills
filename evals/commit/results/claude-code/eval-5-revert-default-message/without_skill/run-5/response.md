I reverted `dd05929` ("worker: retry failed exports") in a new commit, `e89072c worker: revert "retry failed exports"`. The working tree is clean and I didn't run any tests.

**The revert removes exporting entirely, not just the retry.** That commit created `worker/export.py` and `worker/test_export.py` from scratch, so both files are now deleted. Nothing else in the repo references them, so nothing else breaks, but the worker can no longer export.

The likely cause of the duplicates: when a send raised `ConnectionError`, the retry sent it again. The receiving service may already have accepted the first request, so it recorded the export twice. To bring retries back safely, the export needs an idempotency key per invoice so the receiver can drop repeats, or the worker should only retry failures that happen before the request goes out.

Your instructions say to use `/commit`, but that skill isn't available in this session, so I wrote the commit message by hand in the scoped format. I haven't pushed.