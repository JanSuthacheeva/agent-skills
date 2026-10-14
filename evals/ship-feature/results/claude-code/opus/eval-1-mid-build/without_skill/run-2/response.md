The bookmark tags feature is finished: all 5 tasks in `docs/plans/2026-10-14-bookmark-tags.md` are done, ticked and committed. All 17 tests pass, and the commands behave correctly when run for real. There's no lint or type checker set up in this project, so neither was run.

**Commits**
- `50fc213 bm: store tags on bookmarks` - new bookmarks get `tags: []`, and files written before tags existed load as `tags: []`, so no migration is needed.
- `2b2b394 bm: tag bookmarks and list them by tag` - adds `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`. Adding a tag a bookmark already has does nothing.
- `98a02e6 bm: add tag command and list --tag` - the two new CLI commands, with tests for success, an invalid tag, an unknown id and bad usage.
- `532f712 docs: mark bookmark tags plan done` - ticks the last task.

**End-to-end check** (`npm run bm` against a temp `BM_FILE` that started as a file written before tags existed):
- `tag 2 " Work "` prints `tagged 2 work`. Running `tag 2 work` again doesn't add a duplicate.
- `list --tag WORK` lists only the tagged bookmarks. With bookmark 2 tagged `docs`, `list --tag docs` showed only bookmark 2.
- An unknown id prints `no bookmark 9` (exit 1). An invalid tag prints `invalid tag: to do` (exit 2). A non-numeric id or `list --tag` with no tag prints a usage message (exit 2).
- The old bookmark loaded without errors and was saved back with a `tags` field.

**Changes from the plan** (both written into the plan):
- `run` now hands the commands to a private `dispatch` function, so turning the two errors into messages and exit codes happens in one place.
- I added one message the plan didn't specify: `list` with anything other than `--tag <tag>` prints `usage: bm list [--tag <tag>]` and exits 2. A missing tag in `bm tag` gives its usage message, the same as a non-numeric id.

**How it works:** `main` passes the arguments to `run`. For `tag` and `list --tag`, the CLI first cleans up the tag with `normalizeTag` (trim, lowercase, only `a-z`, `0-9` and `-` allowed). It then calls `BookmarkStore::tag` or `listByTag`. The store loads the JSON file (filling in `tags: []` where it's missing), changes or filters it, and saves it. The CLI never touches the file itself.

Nothing is blocked or left open, and nothing has been pushed.