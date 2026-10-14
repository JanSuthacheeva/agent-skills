The bookmark tags feature is built and all five plan tasks are ticked. The full suite passes (17 tests). The project has no lint or type check set up, so only the tests and the end-to-end run were checked.

**Commits**
- `660d822 bm: store tags on bookmarks` - bookmarks now have a `tags` field. Store files written before this change load with no tags, so no migration is needed.
- `05391ab bm: tag bookmarks and list them by tag` - adds `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`. Adding a tag a bookmark already has does nothing.
- `fb14981 bm: add tag command and list --tag` - adds `bm tag <id> <tag>` and `bm list --tag <tag>`.
- `8a4aa15 docs: check bookmark tags end to end` - ticks the last task in the plan.

**End-to-end check:** I ran the real CLI with `npm run bm` against a temp store file that started out in the old format, without tags:
- `bm tag 2 " Work "` printed `tagged 2 work`, and `list --tag WORK` matched it, so tags are trimmed and lowercased.
- Running the same tag a second time changed nothing.
- `bm tag 9 work` printed `no bookmark 9` and exited 1.
- `bm tag x work`, `bm tag 1 "to do"` and `bm list --tag` printed the matching error and exited 2.
- After the run, the file had a `tags` field on every bookmark, including the old one.

**Deviations from the plan**
- I added two error cases the plan didn't list, and wrote them into the plan:
  - `bm tag` with a missing id or tag prints the usage line and exits 2.
  - `bm list` followed by anything other than `--tag <tag>` prints `usage: bm list [--tag <tag>]` and exits 2.
- **Decision for you:** that second case changes existing behaviour. `bm list foo` used to ignore the extra argument and print everything; it now fails. Rejecting unknown arguments seemed safer than ignoring them, but you can revert it to the old lenient behaviour if you prefer.

**How it works:** `main.ts` calls `run()` in `src/cli.ts`, which reads the arguments and cleans up the tag text with `normalizeTag()` before calling the store. All file reading and writing happens in `BookmarkStore`. The two new error types are caught in one place in `run()`, which prints the message and picks the exit code: 1 for an unknown bookmark, 2 for an invalid tag.

Nothing is pushed. The next steps would be the `review-changes` skill, then `write-merge-request`.