I committed the staged changes as `c4d27d2`: `api: invoices!: derive currency from account`.

The commit removes the `currency` query parameter from `GET /invoices/<id>`. The currency now always comes from the invoice's account. This breaks existing clients, so I marked the subject with `!` and added a `BREAKING CHANGE:` footer. It tells clients to stop sending the parameter and read `currency` from the response instead. The README update is in the same commit.

There was no `/commit` skill in the available list, so I wrote the message myself in the scoped format.