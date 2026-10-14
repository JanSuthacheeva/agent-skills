I reverted `3a0482e` ("worker: retry failed exports"). The revert is commit `6977510` on `main`, with the message "worker: revert retry failed exports".

The revert removes `worker/export.py` and `worker/test_export.py`. Both files were added by that commit, so they no longer exist. I didn't run any tests, and I didn't check whether anything else imports those files.

There's no `/commit` skill in this session, so I made the commit with plain git. I rewrote git's default `Revert "..."` message into the `<scope>: <description>` format.