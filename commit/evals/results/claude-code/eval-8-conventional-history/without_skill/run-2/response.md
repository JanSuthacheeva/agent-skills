I committed the staged change as `6fc9136 worker: add jitter to export retry delay`. The change in `worker/export.py` adds a random extra wait of up to one second to the retry delay after a `ConnectionError`.

The message uses the Scoped Commits format (`<scope>: <description>`) I was configured to use. The repo's history uses Conventional Commits instead, which would be `fix(worker): add jitter to export retry delay`. If you want to match the history, I can reword the commit, since it hasn't been pushed.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I wrote the commit directly with git.