I split the staged changes into two commits by scope and pushed them to `origin/main`. I couldn't use the `/commit` skill your instructions call for, because it isn't in the available skills list.

- `411e410` `api: return invoice amount in cents`
- `77fe55c` `worker: send export amount in cents`

`main` had no upstream, so I set it to `origin/main` with the push.

Both commits are the same `amount` to `amount_cents` change, but they touch different scopes. I kept them separate to match your per-scope history.