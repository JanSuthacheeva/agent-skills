I committed the change as `173eb7d` and pushed it to `origin/main`. `main` had no upstream branch, so I set it to track `origin/main`.

```
api, worker: send invoice amounts as integer cents

Float amounts lose precision on serialization. Both the invoice
endpoint and the export payload now send amount_cents instead.

BREAKING CHANGE: the "amount" field is replaced by "amount_cents"
(integer, amount * 100) in the invoice API response and the export
payload. Consumers must read amount_cents and divide by 100.
```

It's one commit because the rename to cents is a single change covering both the API and the worker. The `/commit` skill never pushes, so I ran the push separately because you asked for it.

Converting with `int(x * 100)` cuts off the fraction instead of rounding. A float amount like 19.99 can come out one cent low. Using `round(x * 100)`, or doing the maths in `Decimal`, would avoid that. Want me to fix it?