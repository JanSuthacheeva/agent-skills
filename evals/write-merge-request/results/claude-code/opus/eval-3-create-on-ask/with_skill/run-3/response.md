I pushed the branch and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

I couldn't confirm the published text: `glab mr view 57` printed `glab stub: mr view 57` instead of the MR, so take a quick look at the formatting on the page.

The title is in scoped-commit style because I couldn't read the ticket title (`clickup-axi` returned "task ECOM-88 not found"). If you want it in `<ID> <ticket title>` form, tell me the ticket title and I'll update it.

**Title:** `api: take invoice currency from the account`

**Description:**

```
The `currency` query parameter on `GET /invoices/<id>` let clients ask for totals in a currency we never converted to, so they got EUR amounts labelled USD. The invoice currency now comes from the account, and the parameter is removed.

- The parameter is dropped instead of adding conversion: amounts are only ever computed in the account's currency, so the response now states the currency it is actually in.

Breaking: the `currency` parameter is gone. Clients must stop sending it and read `currency` from the response.

Refs: ECOM-88
```