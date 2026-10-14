I reverted `fb6eec1` ("worker: retry failed exports") in a new commit, `6d0ee24`:

```
worker: revert retry of failed exports

Retrying failed exports causes duplicate exports.

This reverts commit fb6eec177f71bbb36976e38cc055a1cea52ee392.
```

The retry commit created `worker/export.py` and `worker/test_export.py`, so reverting it deletes both files. I didn't check whether anything else imports them, and I didn't run any tests.

Your instructions say to use the `/commit` skill, but it isn't available in this session. I ran `git revert` directly, then changed the default "Revert ..." message to the repo's `scope: description` format.

The commit is local only; I haven't pushed it.