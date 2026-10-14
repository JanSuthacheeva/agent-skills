I committed the two staged changes as one commit and pushed it to `origin/main`. The push needed `--set-upstream` because `main` had no upstream, so it now tracks `origin/main`.

```
api, worker: expose invoice amount in cents

Breaking: the invoice response and the export payload replace
`amount` with `amount_cents`. Consumers must read `amount_cents`
(integer cents) instead of `amount`.
```

I used a single commit because both files make the same change, switching `amount` to `amount_cents`. The body states the breaking change because API and export consumers have to update.