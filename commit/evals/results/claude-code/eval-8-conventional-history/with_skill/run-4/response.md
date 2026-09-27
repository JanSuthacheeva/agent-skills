I committed the staged change to `worker/export.py` on `main` as `656a4bd`:

```
worker: add jitter to export retry delay

A fixed one-second delay makes concurrent failed exports retry in
lockstep and hit the client again at the same moment.
```

Earlier commits in the log start with a type like `feat(...)` or `fix(...)`, but I used the plain `<scope>: <description>` format your commit skill asks for. I didn't push, and there were no other changes in the working tree.