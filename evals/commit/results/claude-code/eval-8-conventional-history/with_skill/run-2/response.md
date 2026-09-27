I committed the staged change to `worker/export.py` as `7d34293`:

```
worker: add jitter to export retry delay

A fixed 1s delay makes failed exports retry in lockstep, hitting the
client again all at once. Random jitter spreads the retries out.
```

The diff doesn't say why the change was made, so the reason in the body is my guess. If you had a different reason, I can reword it with `git commit --amend`.

The scope is `worker` rather than the log's `fix(worker)`, since this commit format leaves out type prefixes. The branch is `main`, so there's no `Refs:` trailer. Nothing else was changed or left unstaged.