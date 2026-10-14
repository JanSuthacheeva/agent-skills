I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

I couldn't confirm the MR text came through intact. `glab mr view 57` only printed a stub line, not the title and description, so check it on the page.

**Title:** `api: take invoice currency from the account`

I couldn't use the ticket title: `clickup-axi` couldn't find ECOM-88. So the title follows the repo's commit format instead.

**Description:**
```
The `currency` query parameter on `GET /invoices/<id>` let clients ask for totals in a currency we never converted to, so they got EUR amounts labelled USD. The response now always uses the account's currency.

BREAKING: the `currency` parameter is gone. Clients must stop sending it and read the currency from the response.

Refs: ECOM-88
```