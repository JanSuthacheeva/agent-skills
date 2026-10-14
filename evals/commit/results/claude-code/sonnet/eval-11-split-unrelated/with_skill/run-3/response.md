I split the changes into three commits, one per file, because they were unrelated. The working tree is clean now.

- `ee3f94b docs: describe the service in readme`
- `59a98fc billing: round invoice totals half-even`
  - The body says half-even rounding avoids the upward bias of half-up across many invoices. That reason is my inference from the code change, so correct it if the real motivation was different.
- `38eb4a6 worker: raise export retries from 3 to 5`

The branch is `main`, so there is no `Refs:` trailer. I didn't run any tests.