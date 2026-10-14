I finished the merge as `b665326` with Git's default message, "Merge branch 'feature/invoice-currency'". Before committing, I checked that no conflict markers were left in `api/invoices.py` or anywhere else in the repo.

Two things differ from your usual setup:
- **Message format:** I kept Git's merge message instead of the `<scope>: <description>` format, since merge commits normally keep it. I can change it to something like `api: merge invoice currency branch` if you'd like.
- **`/commit` skill:** it isn't available in this session, so I ran `git commit` directly.