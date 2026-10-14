I committed the staged changes as `fc2400f api: invoices: drop currency query parameter`.

The commit body explains that `GET /invoices/<id>` now always takes the currency from the invoice's account. It also has a `BREAKING CHANGE:` note telling clients to stop sending `currency` and read it from the response instead. The commit references ECOM-88, the ticket in the branch name.

Your instructions say to use the `/commit` skill, but it isn't installed here. I wrote the message by hand in the `<scope>: <description>` format, matching the repo's existing nested scopes like `api: auth:`.