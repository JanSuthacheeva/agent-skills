I reverted `e62110a` ("worker: retry failed exports") as `b470824`, with the message `worker: revert export retry`. The revert applied cleanly and the working tree is clean. I didn't run any tests or try to reproduce the duplicate exports.

I wrote the message in scoped format instead of git's default `Revert "..."` title. The body notes that the retry caused duplicate exports.

The `/commit` skill isn't in the available skills list, so I committed with plain `git`.

Retries are gone again, so failed exports won't be retried. If you want retries back, they'll need an idempotency guard, such as a dedupe key on the export job, to avoid the duplicates.