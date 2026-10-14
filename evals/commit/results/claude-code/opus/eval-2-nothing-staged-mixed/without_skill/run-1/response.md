I committed the backoff change as `0ae5e5d worker: use exponential backoff for export retries`. I didn't run the tests, and the new one can't pass as the repo stands.

- **What's in it:** `worker/export.py` now retries up to 5 times instead of 3, and waits `0.5 * 2^attempt` seconds between tries instead of a flat second. `worker/test_export.py` adds `test_export_backs_off_exponentially`.
- **Left out:** `debug_dump.txt` and `notes.md` are still untracked. They look like scratch files, so I didn't commit them.
- **Missing test fixtures:** The new test uses a `sleeps` fixture that doesn't exist anywhere in the repo. Neither do `fake_client` and `fake_invoice`, which the existing test also uses, so that one can't run either. There's no `conftest.py` defining them.
- **No `/commit` skill:** Your instructions say to use it, but it isn't installed in this session, so I committed with git directly in the `<scope>: <description>` format.

I can add a `conftest.py` with those fixtures (including a `sleeps` that records calls to a mocked `time.sleep`) so the tests can actually run.