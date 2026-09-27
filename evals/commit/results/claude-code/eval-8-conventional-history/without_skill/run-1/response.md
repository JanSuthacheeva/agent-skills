I committed the staged change as `0aa9c2e worker: add jitter to export retry delay`. It changes the wait between export retries in `worker/export.py` from a flat 1s to a random 1-2s.

- **Message format:** I used the Scoped Commits format (`<scope>: <description>`) I was told to use. This repo's history uses Conventional Commits instead (e.g. `fix(worker): ...`). If you'd rather match the history, I can amend it to `fix(worker): add jitter to export retry delay`.
- **`/commit` skill:** Your CLAUDE.md says to use it, but it isn't installed in this session, so I made the commit directly.