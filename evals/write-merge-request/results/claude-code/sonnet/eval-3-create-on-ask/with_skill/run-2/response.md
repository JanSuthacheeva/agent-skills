I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

I couldn't confirm the description on the MR page. `glab mr view` only returned "glab stub: mr view" here, so I never saw the title or description as GitLab stored them.

**Title:** `api: take invoice currency from the account`. `clickup-axi` couldn't find ECOM-88, so I used a scoped-commit title instead of `ECOM-88 <ticket title>`.

**Description:**
> The currency query parameter let clients ask for totals in a currency we never converted to, so they got EUR amounts labelled USD. The invoice endpoint now always reports the account's currency.
>
> Breaking: `GET /invoices/<id>` no longer accepts `currency`. Clients must stop sending it and read `currency` from the response.
>
> Refs: ECOM-88

There are no deploy steps and no review guide, since the diff is one commit touching two files.