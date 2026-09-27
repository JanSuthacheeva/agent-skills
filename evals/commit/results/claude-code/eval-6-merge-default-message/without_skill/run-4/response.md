I finished the merge and committed it on `main` as `cd6a72c api: merge feature/invoice-currency`.

- I checked `api/invoices.py` first and there were no conflict markers left.
- The merge brings in one commit, `70912c0 api: take invoice currency from the account`. That replaces the `usd` default that `2aedd2e` had added on `main`.
- I changed Git's default "Merge branch ..." message so it matches the `<scope>: <description>` format the rest of the history uses.

I didn't run any tests after the merge. It's only a local commit for now - tell me if you want it pushed.