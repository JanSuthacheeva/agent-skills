I committed the change, but I did not push it. The commit skill never pushes, and you didn't tell me to override that. Run `git push` yourself if you want it pushed.

It's one commit on `main` (2207a47), because both staged files are the same change: the invoice amount is now sent in cents.

```
api, worker: send invoice amount in cents

Floating point amounts drifted when summed downstream. Integer
cents avoid the rounding errors.

BREAKING: the invoice response and export payload field `amount`
is now `amount_cents` (integer). Consumers must read `amount_cents`
and divide by 100 if they need the decimal value.
```

The reason in the body is my inference from the diff, not something you told me, so check that it matches your intent. The breaking-change note is real: anything reading `amount` from the invoice response or export payload will break.