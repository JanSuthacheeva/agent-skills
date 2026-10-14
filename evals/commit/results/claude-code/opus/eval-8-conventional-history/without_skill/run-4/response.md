I committed the staged change as `3d55939 worker: add jitter to export retry backoff`. The change adds a random 0-1s delay to each retry wait in `worker/export.py`.

- **Different message style:** your setup asks for `<scope>: <description>`, so I used that. The repo's existing commits use a different style (like `fix(worker): ...`), so this one won't match them.
- **No `/commit` skill:** your instructions say to always use it, but it isn't installed in this session, so I committed with plain git.