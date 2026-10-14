Committed as 11a6119:

```
worker: back off exponentially when retrying failed exports

A fixed 1s sleep hammered the export endpoint while it was down.
Delay now doubles per attempt from a 0.5s base, and the retry count
rises from 3 to 5 to cover the longer recovery window.
```

I staged only `worker/export.py` and `worker/test_export.py`. I left out `debug_dump.txt` (a debug payload dump) and `notes.md` (a TODO note), which are untracked and unrelated. The branch name has no ticket ID, so there's no `Refs:` trailer.

I wrote the "why" in the body myself, since the diff doesn't say it. That includes the claim that the fixed sleep was hammering the endpoint. Amend the message if that isn't the real reason.