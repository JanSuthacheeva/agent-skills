I finished the merge as `ebfb908 Merge branch 'feature/invoice-currency'`. I kept git's default merge message rather than the `<scope>: <description>` format, since that's the usual convention for merge commits.

Before committing, I checked that no conflict markers were left. In `api/invoices.py`, your resolution keeps the feature branch's version, so the invoice currency now comes from the account (`invoice.account.currency`). This drops main's `?currency=` request parameter and its "USD" default.

Your instructions say to use the `/commit` skill, but it isn't available in this session, so I committed with plain git.