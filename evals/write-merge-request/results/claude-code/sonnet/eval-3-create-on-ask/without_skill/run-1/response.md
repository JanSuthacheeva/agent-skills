I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `api: take invoice currency from the account`. I used Scoped Commits because `clickup-axi` couldn't find ECOM-88, so I couldn't use the ticket title.
- **Description:** It explains the EUR-labelled-USD bug and lists the changed files. It calls out the breaking change: clients must stop sending `currency` and read it from the response.