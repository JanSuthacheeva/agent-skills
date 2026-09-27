The merge is done: `8ddcdf0 Merge branch 'feature/invoice-currency'` is now on `main`.

- **No conflict markers left:** I searched the repo and found none. Your resolution in `api/invoices.py` keeps the feature branch's version, so the currency now comes from `invoice.account.currency` instead of the `currency` request parameter that defaulted to USD.
- **Commit message:** I kept git's default merge message rather than rewriting it into `<scope>: <description>` form. The two commits being merged already use that format.
- **`/commit` skill:** It isn't installed in this session, so I committed directly with `git commit --no-edit`.

I didn't run any tests after the merge.