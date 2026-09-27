I committed the staged changes as `799d076`, with the message `api: invoices: drop currency query parameter`.

- **Message body:** it gives the reason for the change: clients could ask for totals in a currency they were never actually converted to, so the currency now always comes from the invoice's account.
- **Breaking change:** a `BREAKING CHANGE:` footer says that `GET /invoices/<id>` no longer accepts the `currency` query parameter. Clients must stop sending it and read `currency` from the response instead.
- **Ticket:** `Refs: ECOM-88`, taken from the branch name.
- **Files:** both `README.md` (the docs for this) and `api/invoices.py` went into the same commit.

Your instructions say to use a `/commit` skill, but none is installed in this session, so I wrote the message myself in the `<scope>: <description>` format your earlier commits use.