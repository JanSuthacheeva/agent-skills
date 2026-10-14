I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `api: take invoice currency from the account`. The branch name has the ticket ID ECOM-88, but clickup-axi returned "task ECOM-88 not found". So I couldn't use the ticket's title and used the scoped commit message instead.
- **Description:** what changed, why (clients were getting EUR amounts labelled as USD), the files changed, and `Refs: ECOM-88`.
- **Breaking change:** `GET /invoices/<id>` no longer accepts the `currency` parameter. It's called out in its own section of the description so reviewers and API clients see it.