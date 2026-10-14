I committed the staged change as `20e6b32 worker: add jitter to export retry delay`. When an export fails, `worker/export.py` now waits a random 1-2 seconds before retrying instead of exactly 1 second.

I used the `<scope>: <description>` format I was configured with. The repo's history uses a different style, so in that style this would have been `fix(worker): ...`. If you want it to match, I can amend the message.

Your CLAUDE.md says to use the `/commit` skill, but it isn't installed in this session, so I committed directly with git.