I committed the staged changes as `283b0e7`: `api: invoices: take currency from the account`.

The commit drops the `currency` query parameter from `GET /invoices/<id>`. The response now always uses the owning account's currency. The README change documenting this is in the same commit.

Because clients that send `currency` will now need to change, I marked it with a `BREAKING CHANGE:` footer in the message body.

The `/commit` skill your instructions call for isn't in this session's skill list, so I wrote the commit by hand in the Scoped Commits format.