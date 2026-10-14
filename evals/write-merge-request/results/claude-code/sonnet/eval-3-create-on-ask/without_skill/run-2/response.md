I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** "api: take invoice currency from the account". I couldn't read ticket ECOM-88 with clickup-axi (it returned "task not found"), so I used the commit's title instead of the ticket title.
- **Description:** it explains that the `currency` query parameter is removed and clients must read `currency` from the response. It's flagged as a breaking change and references ECOM-88.
- **Source branch:** it will be deleted when the MR is merged.