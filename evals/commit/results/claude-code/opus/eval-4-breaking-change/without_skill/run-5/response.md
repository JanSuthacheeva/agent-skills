I committed the staged changes as `032f52b` on `ECOM-88-drop-currency-param`:

```
api: invoices: drop currency query parameter

GET /invoices/<id> now always returns totals in the owning account's
currency. The currency query parameter let clients label totals with a
currency they were never converted to.

BREAKING CHANGE: the currency query parameter is now ignored. Clients
must stop sending it and read currency from the response.

Refs: ECOM-88
```

- **Breaking change:** clients that send `currency` will now get the account's currency back, so I flagged it in a `BREAKING CHANGE` section.
- **One commit:** the README update and the code change describe the same change, so they're committed together.
- **Wording fix:** the first version said the parameter is "no longer accepted," which was wrong because the code just ignores it. I amended the local commit to say "ignored."

Your CLAUDE.md says to use the `/commit` skill, but it isn't installed in this session. I wrote the message by hand instead, following the repo's `scope: subscope: description` style.