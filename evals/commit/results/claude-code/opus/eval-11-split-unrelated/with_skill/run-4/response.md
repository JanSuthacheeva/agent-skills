The three changes weren't related, so I made a separate commit for each:

```
billing: use banker's rounding for invoice totals
worker: raise export retries from 3 to 5
docs: describe the service in the readme
```

None of them has a body, because I don't know why rounding switched from round-half-up to round-half-even or why retries went up. The billing one changes invoice totals that end in exactly half a cent. If you tell me the reason, I can amend that commit to add it.

The working tree is clean now. I didn't add a `Refs:` trailer because you're on `main`, which has no ticket ID in its name.