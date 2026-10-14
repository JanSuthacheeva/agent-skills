I reverted the export retry commit (`bf0eb10`). The new commit is `9ad0c31`, titled `worker: revert "retry failed exports"`.

That commit created `worker/export.py` and its test from scratch, so the revert deletes both files and the export function goes away entirely. Nothing else in the repo uses that module, and no later commits changed those files. I didn't run any tests.

You'll need a new export function that doesn't resend. The old one retried whenever the connection dropped, even if the client had already received the export, which is a likely cause of the duplicates. An idempotency key on `client.send` would let it retry safely.

Your instructions say to use the `/commit` skill, but it isn't available in this session, so I made the commit with git directly in the `<scope>: <description>` format.