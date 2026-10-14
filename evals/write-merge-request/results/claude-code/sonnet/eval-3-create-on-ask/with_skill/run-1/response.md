I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `api: take invoice currency from the account`. I couldn't read the ticket title (`clickup-axi` said ECOM-88 wasn't found), so I used a scoped title instead of the ticket's.
- **Description:** It covers the reason (clients got EUR amounts labelled USD), the breaking removal of the `currency` parameter and how clients should migrate, and `Refs: ECOM-88`.
- **Not checked:** `glab mr view` only returned a stub message, so I couldn't confirm the stored title and description match what I sent.