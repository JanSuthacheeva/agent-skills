I committed the changes as three separate commits on `main`, since they were unrelated:

- `0897390 billing: use banker's rounding for invoice totals`
- `c20e49a worker: raise export retries to 5`
- `6cd3839 docs: describe service in readme`

The rounding change affects money: a total that ends in exactly half a cent now rounds to the nearest even cent, so 0.125 becomes 0.12 instead of 0.13. No tests were run.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I followed the existing `scope: description` style instead. Nothing has been pushed.