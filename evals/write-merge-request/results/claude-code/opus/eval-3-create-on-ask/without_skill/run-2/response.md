I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `api: take invoice currency from the account`. The branch has a ticket ID, but `clickup-axi` couldn't find ECOM-88, so I used the commit-style title instead of the ticket title.
- **Description:** explains the currency bug that was fixed and flags the breaking change: the `currency` query parameter is removed. It ends with `Refs: ECOM-88`.

Before creating the MR, a `glab mr create --help` call also printed this same MR URL. `glab mr list` showed no open MRs at that point, so I think only one MR exists, but check that there isn't a duplicate.