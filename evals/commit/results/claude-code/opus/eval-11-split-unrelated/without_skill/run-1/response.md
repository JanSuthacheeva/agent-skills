The changes weren't related to each other, so I committed them as three separate commits:

- `76efc17 billing: use banker's rounding for invoice totals` - invoice totals now round half-to-even instead of half-up, so amounts ending in exactly half a cent can come out one cent different.
- `9bca775 worker: raise export retries to 5`
- `9cff884 docs: describe service in readme`

Nothing is left uncommitted. Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I wrote the commits by hand in the same `<scope>: <description>` format as your existing history.