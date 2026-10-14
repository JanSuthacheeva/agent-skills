I committed the two staged files as one commit and pushed it to `origin/main`.

```
api, worker: send invoice amount as integer cents

Floating point amounts caused rounding mismatches downstream. The
invoice response and export payload now carry amount_cents instead
of amount.

BREAKING: consumers must read amount_cents (integer cents)
instead of amount.
```

- **Why one commit:** both files make the same change (`amount` becomes `amount_cents`), so I didn't split them by scope.
- **Body:** I added a breaking-change note because the API field was renamed.
- **No `Refs:` trailer:** the branch is `main`, so there is no ticket ID.
- **Upstream:** a plain `git push` failed because `main` had no upstream branch. I ran `git push --set-upstream origin main`, so `main` now tracks `origin/main`.

The commit skill says never to push, but you asked for a push, so I pushed.