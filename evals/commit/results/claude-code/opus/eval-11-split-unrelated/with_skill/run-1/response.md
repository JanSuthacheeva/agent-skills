The three changes weren't related to each other, so I made three separate commits on `main`:

```
billing: use banker's rounding for invoice totals
worker: raise export retries from 3 to 5
docs: describe the service in readme
```

- **`billing`:** invoice totals now round with `ROUND_HALF_EVEN` instead of `ROUND_HALF_UP`.
- **`worker`:** the default number of export retries is now 5 instead of 3.
- **`docs`:** the README has a one-line description of the service.

The commit messages have no body because I didn't know why the rounding and retry changes were made. If you tell me, I can add the reason to those commits.

Nothing is left uncommitted, and nothing was pushed.