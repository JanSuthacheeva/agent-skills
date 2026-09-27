I committed the pagination work on `feature/invoice-pagination` as `e067e08 api: paginate invoice list endpoint`. It includes `api/invoices.py` and the new `api/test_invoices.py`. I didn't run the tests before committing, and nothing is pushed.

- **Left out:** `worker/export.py` has an unrelated half-finished comment ("WIP: try jitter here, not done yet"), so it's still uncommitted.
- **No `/commit` skill:** your instructions say to use it, but it isn't installed here. I followed the repo's existing `<scope>: <description>` style instead.
- **Bug in the new code:** `list_invoices` doesn't check the `page` parameter.
  - `?page=0` gives a start of -50, so it returns the last 50 invoices instead of an error or the first page.
  - `?page=abc` raises an error, which likely becomes a 500.

  Want me to fix that and add tests for it?