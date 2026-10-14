I committed the staged changes and pushed them to `origin/main` as `27d26af api, worker: send invoice amounts as integer cents`. `main` now tracks `origin/main`.

I wrote the commit by hand because the `/commit` skill your instructions mention isn't installed in this session. Both files make the same change (amounts sent as cents), so I put them in one commit with both scopes in the message.

Two problems in this change you should know about:
- **Wrong amounts:** `int(x * 100)` can come out one cent short, because decimal amounts aren't stored exactly. For example, `int(19.99 * 100)` gives `1998`, not `1999`. Using `round()` instead of `int()` would fix it, or `Decimal` if the totals can be decimals.
- **Breaking change:** both the API response and the export payload now use `amount_cents` instead of `amount`. Anything that reads those will need updating.