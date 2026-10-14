I committed the staged changes as `efa5001`. There is no `commit` skill in this session, so I ran `git commit` directly instead of using `/commit` as your instructions say.

The message is `api: invoices!: take currency from the account`. I marked it as breaking with `!` and a `BREAKING CHANGE:` footer. `GET /invoices/<id>` no longer accepts the `currency` query parameter, and the currency now comes from the owning account. The commit includes the README update describing this.

I didn't run any tests.