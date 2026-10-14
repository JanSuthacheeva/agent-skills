I committed the staged changes as `e8328c9`: `api: invoices!: drop currency query parameter`.

The `!` and a `BREAKING CHANGE:` footer mark it as breaking, because `GET /invoices/<id>` no longer accepts the `currency` query parameter. The invoice currency now always comes from the owning account. The commit includes the README note telling clients to drop the parameter and read `currency` from the response.

I didn't use the `/commit` skill. It isn't in the available skills list, so I wrote the message directly in the scoped format.