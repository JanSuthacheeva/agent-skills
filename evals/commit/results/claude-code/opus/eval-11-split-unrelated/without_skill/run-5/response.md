The three changes weren't related, so I committed each one separately. The working tree is now clean.

- `0f93dda billing: use banker's rounding for invoice totals`: invoice totals now round with `ROUND_HALF_EVEN` instead of `ROUND_HALF_UP`. Totals that land exactly on a half cent will now round to the even cent, so some will come out one cent lower than before.
- `86f37b2 worker: raise export retries from 3 to 5`
- `fc0e170 docs: describe service in readme`

Your instructions say to use the `/commit` skill, but it isn't installed in this session. I wrote the commits by hand in the repo's existing `<scope>: <description>` style instead.