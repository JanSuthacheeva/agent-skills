I committed the backoff change as `6a28550`:

```
worker: back off exponentially between export retries
```

It includes `worker/export.py` and `worker/test_export.py`. I didn't run the tests before committing. I left `debug_dump.txt` and `notes.md` out because they look like scratch files, and they're still untracked. There's no ticket ID in the branch name, so the commit has no `Refs` line.

Two things to check in the committed code:
- **Wasted wait before failing:** after the last failed try it still sleeps before raising. With the defaults that's 8s spent before the export fails anyway. I can add a check to skip the sleep on the last try if you want.
- **More retries:** the default went from 3 to 5, so a failing export now waits about 15.5s in total before it gives up.