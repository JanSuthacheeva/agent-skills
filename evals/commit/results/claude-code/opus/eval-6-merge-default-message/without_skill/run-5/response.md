I finished the merge: `0a1f523 api: merge branch 'feature/invoice-currency'` on `main`.

- Before committing, I checked `api/invoices.py`: no conflict markers were left and nothing was still unmerged.
- I didn't keep git's default merge message. I changed it to the `<scope>: <description>` format and used the `api:` scope that both merged commits use. I first committed it with an `invoices:` scope, then amended it to `api:` to match. That rewrite only touched your local merge commit.
- Your instructions say to use the `/commit` skill, but it isn't available in this session, so I made the commit with git directly.
- I didn't run any tests on the merged code. The two branches changed the same thing in different ways (one defaults invoice currency to USD, the other takes it from the account), so it's worth checking that your resolution behaves the way you want.