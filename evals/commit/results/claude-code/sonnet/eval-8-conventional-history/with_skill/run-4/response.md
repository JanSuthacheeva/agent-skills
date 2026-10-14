Committed `ddc8a7a` on `main`:

```
worker: add jitter to export retry delay

Fixed one-second sleeps made concurrent exports retry in lockstep
after a connection failure.
```

I left out the `feat`/`fix` type prefix that the log uses, because the commit skill's rules forbid it. The branch name has no ticket ID, so there is no `Refs:` trailer.