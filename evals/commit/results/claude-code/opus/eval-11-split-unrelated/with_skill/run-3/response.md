I made three commits on `main`, one for each unrelated change, and the working tree is now clean:

```
billing: round invoice totals half-even
worker: raise export retries from 3 to 5
docs: describe the service in readme
```

None of them has a body explaining why the change was made, because the diffs don't say. If you tell me why rounding moved to half-even or why exports now retry 5 times, I can add that to the message. Nothing was pushed.