The changes were unrelated, so I made three separate commits on `main`. The working tree is clean.

```
billing: round invoice totals half-even instead of half-up
worker: raise export retries from 3 to 5
docs: describe the service in readme
```

None of the commits has a body because the diffs don't say why the rounding mode or the retry count changed. If you tell me, I can add that reasoning to the messages.