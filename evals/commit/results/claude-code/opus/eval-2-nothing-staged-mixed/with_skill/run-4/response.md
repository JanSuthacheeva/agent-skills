I committed the backoff as `27390ea` on `feature/export-backoff`:

```
worker: back off exponentially between export retries
```

The commit includes `worker/export.py` and `worker/test_export.py`. I didn't run the tests.

The default number of retries also went up from 3 to 5. The commit message doesn't mention this. If that's a change in behavior you want on record, I can reword the message.

I left out `debug_dump.txt` and `notes.md`, which aren't tracked and look unrelated to this work.