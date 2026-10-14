I pushed the branch and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

I couldn't confirm that the title and description came through correctly. `glab mr view 57` only printed a stub line, not the MR's contents, so it's worth a quick look on the web page.

**Title:** `api: take invoice currency from the account`

I couldn't read the ECOM-88 ticket title (ClickUp said "task ECOM-88 not found"), so I didn't use the `ECOM-88 <ticket title>` format. The title follows the commit's own scoped format instead.

**Description:**
```
The `currency` query parameter on `GET /invoices/<id>` let clients ask for totals in a currency we never converted to, so they got EUR amounts labelled USD. The invoice now always reports the account's currency and the parameter is removed.

Breaking: the `currency` parameter is gone. Clients must stop sending it and read the currency from the response.

Refs: ECOM-88
```

There was no MR template in the repo, and the working tree had no uncommitted changes.