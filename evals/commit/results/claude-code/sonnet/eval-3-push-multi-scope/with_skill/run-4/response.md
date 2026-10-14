The commit and push both went through. I committed the two staged files, then pushed `main` to `origin` and set it to track `origin/main`. The first plain `git push` failed because `main` had no upstream.

```
api, worker: switch invoice amount to integer cents

Float amounts caused rounding drift between the API and the export
payload. Both now send amount_cents as an integer.

BREAKING: the invoice response and export payload no longer have
"amount". Consumers must read "amount_cents" (value * 100).
```

I treated the two files as one change, since both switch `amount` to `amount_cents`. The commit skill says never to push, but you asked for the push, so I did it. The rounding-drift reason in the body is my inference from the diff, so edit it if the real motivation was different.