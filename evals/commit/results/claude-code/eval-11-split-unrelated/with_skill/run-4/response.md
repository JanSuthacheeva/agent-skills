The three changes had nothing to do with each other, so I made three separate commits:

```
billing: round invoice totals half-even instead of half-up
worker: raise export retries from 3 to 5
docs: describe the service in the readme
```

The working tree is now clean. I left out a body explaining why because the diffs don't show the reasons. If there's context worth recording, like why rounding changed to half-even, I can add it with an amend. You're on `main`, so there's no ticket ID for a `Refs:` line, and nothing was pushed.