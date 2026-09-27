The changes weren't related to each other, so I made three separate commits. The working tree is now clean.

- `ec6ef00 billing: round invoice totals half-even` - `ROUND_HALF_UP` becomes `ROUND_HALF_EVEN` in `billing/totals.py`. This changes the invoice amounts customers see: a total like 1.125 now rounds to 1.12 instead of 1.13.
- `5d38469 worker: raise export retries to 5` - the default retry count in `worker/export.py` goes from 3 to 5.
- `0cf23aa docs: describe service in readme` - adds a one-line description of the service to the README.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I committed with plain git, using the same `<scope>: <description>` style as the earlier commits.