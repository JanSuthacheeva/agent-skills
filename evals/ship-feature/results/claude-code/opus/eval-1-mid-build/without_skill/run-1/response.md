Bookmark tags are built: all five tasks in the plan are done and committed. The 18 tests pass, and the commands work end to end when run through the real CLI. The project has no lint or type checker set up, so tests were the only automated check.

**Commits**
- `dce3cac` `bm: store tags on bookmarks`: bookmarks now have a `tags` list. Files saved before tags existed load with no tags, so no migration is needed.
- `941df2e` `bm: tag bookmarks and list them by tag`: adds `BookmarkNotFoundError`, `tag()` and `listByTag()` to the store. Adding a tag a bookmark already has does nothing.
- `3023b65` `bm: add tag command and list --tag`
- `d2e9507` ticks the last task in the plan.

**End-to-end check:** I ran the CLI (`node src/main.ts`) against a temp store that started with a bookmark saved before tags existed, and checked the saved file afterwards.
- `tag 2 ' Work '` prints `tagged 2 work`, and tagging it again leaves only one `work`.
- `list --tag WORK` lists only the tagged bookmarks, including the old one.
- `tag 9 work` prints `no bookmark 9` and exits 1.
- `tag 2 'to do'` prints `invalid tag: to do` and exits 2.
- `tag x work` and `list --tag` with no tag both print a usage line and exit 2.

**Changes from the plan** (both are recorded in the plan file):
- `bm list` with `--tag` but no tag, or with any other argument, now prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover these cases. The wording is my choice, so change it if you'd prefer something else.
- `bm tag` also rejects a missing or extra argument with its usage line. This means `bm tag 1 to do` without quotes is a usage error, not an invalid tag.

**How it works:** `run()` in `src/cli.ts` now wraps the existing command switch in one try/catch. That catch is the only place errors become messages and exit codes, as `AGENTS.md` asks. `tag` and `list --tag` clean up the tag with `normalizeTag()` before calling the store. The store loads the file, changes it and saves it.

Nothing is pushed. The next steps would be a review in a fresh context (`/review-changes`) and then the merge request.