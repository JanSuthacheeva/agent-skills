I committed the staged change as `e9fb61c worker: add jitter to export retry delay`. In `worker/export.py`, a failed export now waits a random 1-2 seconds before retrying instead of exactly 1 second.

This repo's earlier commits use the `type(scope):` style (e.g. `fix(worker): ...`). I used the `<scope>: <description>` format I was set up to use, so this commit doesn't match them. If you'd rather it fit the history, I can reword it to `fix(worker): add jitter to export retry delay`.

Your instructions say to use the `/commit` skill, but it isn't installed here, so I made the commit with git directly.