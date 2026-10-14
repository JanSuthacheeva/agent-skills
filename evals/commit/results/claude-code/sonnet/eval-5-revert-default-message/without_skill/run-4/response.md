I reverted the export retry commit (`9c7aac0`, "worker: retry failed exports"). The revert is commit `f82b06a`, "worker: revert retry failed exports". I didn't run any tests.

That commit created `worker/export.py` and `worker/test_export.py`, so the revert deletes both files. Nothing else in the repo references "export", so nothing else should break. If you only wanted the retry logic removed and the export worker kept, tell me and I'll redo it.

The `/commit` skill isn't available in this session, so I made the commit with plain git. I used your `<scope>: <description>` format for the message.