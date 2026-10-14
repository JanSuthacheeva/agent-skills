I reviewed the branch against the plan, fixed six deviations and committed them as `6063008`. `npm test` passes (15 tests). I also ran `add`, `tag` and `list --tag` against a temp store file, and the output and exit code matched the plan. The `/commit` skill wasn't available, so I committed with plain git.

What I fixed:
- **Wrong exit code:** an unknown id in `tag` returned 2. The plan and `AGENTS.md` say 1.
- **Duplicate tags:** tagging a bookmark with a tag it already had pushed a second copy. The plan says this is a no-op, so `BookmarkStore::tag` now skips it and doesn't rewrite the file.
- **Method name:** `listTagged` is now `listByTag`, as the plan specifies.
- **Normalizing the filter:** `list --tag " Work "` found nothing because the filter was never normalized. `listByTag` and the CLI now normalize it, and an invalid tag prints `invalid tag: <raw>` with exit 2.
- **Id parsing:** `Number()` accepted odd input such as an empty string (read as 0). The id must now be digits only, otherwise the usage message and exit 2.
- **Missing tests:** I added the ones the plan lists for a duplicate tag, an unknown id (store and CLI), a non-numeric id, and `list --tag` with normalization.

One thing for you to decide: the plan's task list was already all ticked, even though the duplicate and unknown-id tests were missing. I left the checkboxes as they were.