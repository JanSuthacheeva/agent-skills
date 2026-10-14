I split the three unrelated changes into three commits on `main`:

- `docs: describe the service in readme`
- `billing: round invoice totals half-even`. The body says half-up rounding biased totals upward across many invoices. That reason is my inference from the diff, so edit it if the real reason differs.
- `worker: raise export retries to 5`

There was no ticket ID in the branch name, so I added no `Refs:` trailer. Nothing was pushed.