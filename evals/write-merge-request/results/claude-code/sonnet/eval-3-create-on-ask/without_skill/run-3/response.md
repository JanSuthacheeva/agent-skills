I pushed `ECOM-88-drop-currency-param` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

`clickup-axi` couldn't find ECOM-88, so I couldn't use the ticket title. The MR title is `api: take invoice currency from the account`, taken from the commit message.

The description covers:
- **What changed:** the `currency` query parameter is removed, and the response always uses the account's currency.
- **Why:** the parameter let clients get EUR amounts labelled USD.
- **Breaking change:** clients must stop sending `currency` and read it from the response.

It also references ECOM-88.