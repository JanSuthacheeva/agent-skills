The three changes weren't related to each other, so I made three separate commits on `main`:

```
billing: round invoice totals half-even instead of half-up
worker: raise export retries from 3 to 5
docs: describe the service in readme
```

The working tree is clean. None of the commits has a body because I don't know why the rounding mode or retry count changed. If there's a reason worth recording, especially for the rounding change, I can amend the messages. Nothing was pushed.