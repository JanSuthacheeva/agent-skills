I committed the change as `8af7686 api, worker: report invoice amounts as integer cents` and pushed it to `origin/main`. The working tree is clean.

- **One commit:** I kept both files together because they make the same change, switching `amount` to `amount_cents` in both the API response and the export payload.
- **No `/commit` skill:** your CLAUDE.md says to use it, but it isn't available in this session, so I wrote the message by hand in the repo's `scope: description` style.
- **Breaking change:** anything that reads `amount` from the invoice endpoint or from export payloads will stop finding it. Those consumers need to switch to `amount_cents`.