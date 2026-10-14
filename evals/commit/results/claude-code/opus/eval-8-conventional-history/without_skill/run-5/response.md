I committed the staged change as `554acf8 worker: add jitter to export retry delay`. In `worker/export.py`, the wait between retries is now a random 1-2 seconds instead of exactly 1 second.

Two things to know:
- **Commit format:** I used the `<scope>: <description>` format I was configured with. That doesn't match the repo's existing history, which uses Conventional Commits (`fix(worker): ...`). If you want it to match, I can amend it to `fix(worker): add jitter to export retry delay`.
- **`/commit` skill:** Your instructions say to always use it, but it isn't available in this session, so I committed directly.