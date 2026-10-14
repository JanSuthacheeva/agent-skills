I split the changes into three commits because they're unrelated to each other:

```
billing: round invoice totals half-even instead of half-up
worker: raise export retries from 3 to 5
docs: describe the service in the readme
```

The working tree is clean now. None of the messages has a body explaining why the change was made, because I don't know your reasons. If you tell me why rounding and retries changed, I can amend those commits to include it.