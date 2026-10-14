The branch is pushed and the MR is open against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

`glab mr view` only returned a stub message here, so I couldn't check that the title and description came through as written.

I used the scoped title `api: take invoice currency from the account`, because `clickup-axi` couldn't find ECOM-88 and I couldn't read the ticket title.

The description says the `currency` parameter is removed because we never convert to another currency, notes the breaking change for clients, and ends with `Refs: ECOM-88`.

The description also says old clients that still send `currency` are ignored rather than rejected. I inferred that from the diff, so check it matches your intent.

There was nothing uncommitted and no MR template.