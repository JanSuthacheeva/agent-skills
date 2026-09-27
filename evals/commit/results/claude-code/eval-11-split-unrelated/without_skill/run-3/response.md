The three changes had nothing to do with each other, so I made three commits on `main` instead of one:

- `f55913e billing: use banker's rounding for invoice totals`
- `3328dcf worker: raise default export retries to 5`
- `8a91d8b docs: describe service in readme`

The working tree is clean and nothing has been pushed.

Your instructions say to use the `/commit` skill, but it isn't installed in this session. I wrote the messages by hand in the `<scope>: <description>` format your recent history uses.

Switching billing to banker's rounding (round-half-to-even) changes invoice amounts that end in exactly half a cent. You may want a test that covers that case.