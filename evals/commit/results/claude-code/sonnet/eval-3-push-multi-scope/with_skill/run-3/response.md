Committed and pushed to `origin/main`, which now tracks upstream. The commit skill says never to push, so I pushed only because you asked. The first plain `git push` failed because `main` had no upstream, so I reran it with `--set-upstream origin main`.

Commit `fb40f22`:

```
api, worker: send invoice amount as integer cents

Float amounts risk rounding drift between the API and the export
client. The invoice response field is renamed from amount to
amount_cents, so API consumers must read amount_cents instead.
```

It covers both staged files as one change. The API response field is now `amount_cents`, so I put the migration note in the body.