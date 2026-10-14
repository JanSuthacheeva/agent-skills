I split the changes into three commits, one per unrelated change. Nothing was staged, so I staged each file myself. The working tree is clean now.

- `docs: describe the service in readme`
- `billing: round invoice totals half-even`, with a body saying half-even rounding avoids systematic upward bias across many invoices. I inferred that reason from the diff, so correct it if the real one differs.
- `worker: raise export retries to 5`

The branch is `main`, so there are no `Refs:` trailers. I didn't push.