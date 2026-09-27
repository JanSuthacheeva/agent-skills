I reverted `dd05929` ("worker: retry failed exports") as commit `f9b17d6`, message `worker: revert "retry failed exports"`. Nothing has been pushed.

- **What it removes:** that commit only added `worker/export.py` and `worker/test_export.py`, and nothing since has touched either file. The revert deletes both, so `worker/` no longer has an export function or a test for it.
- **Why it caused duplicates:** the retry loop re-sent the export whenever it got a `ConnectionError`. If the connection dropped after the remote side had already received the export, the retry sent it a second time. The commit message says this.
- **Not checked:** I didn't reproduce the duplicate exports first, and I didn't run the test suite after the revert.
- **Your `/commit` skill:** it wasn't in this session's skill list, so I made the commit by hand in the scoped `<scope>: <description>` format, with no co-author line.

If you still want retries, the send needs to be idempotent (for example, an idempotency key per invoice) so the remote side can drop repeat sends.