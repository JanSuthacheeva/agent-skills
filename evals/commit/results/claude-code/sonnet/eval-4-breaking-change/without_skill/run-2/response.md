I committed the staged changes as `727d891`: `api: invoices!: derive currency from account`.

The commit removes the `currency` query parameter from `GET /invoices/<id>`. Currency now comes from the owning account. Because this breaks existing clients, I marked it with `!` and added a `BREAKING CHANGE` footer. The README change is in the same commit.

The `/commit` skill isn't in the available skills list, so I wrote the commit by hand in the Scoped Commits format.