The three changes had nothing to do with each other, so I made three commits on `main`. The working tree is clean now.

1. `billing: use banker's rounding for invoice totals`: invoice totals now round with `ROUND_HALF_EVEN` instead of `ROUND_HALF_UP`.
2. `worker: raise export retries from 3 to 5`: `export()` now retries up to 5 times by default instead of 3.
3. `docs: describe the service in readme`: adds a one-line description of the service to the README.

The commit messages don't say why each change was made, since the changes didn't show it. The rounding change affects money: amounts that end exactly on a half cent now round to the even cent. For example, 0.125 becomes 0.12 where it used to be 0.13. If you tell me the reason, I can add a body explaining it to that commit before you push.