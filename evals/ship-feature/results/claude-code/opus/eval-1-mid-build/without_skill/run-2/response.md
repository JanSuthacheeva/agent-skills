The bookmark tags feature is built: all 5 tasks in the plan are ticked and committed, and all 17 tests pass. The project has no lint or type-check setup, so tests are the only check.

**Commits**
- `06df4cb bm: store tags on bookmarks` - bookmarks now have a `tags` field. Store files written before tags existed load with empty tags, so no migration is needed.
- `a051e86 bm: tag bookmarks and list them by tag` - adds `BookmarkNotFoundError`, `BookmarkStore::tag` and `listByTag`. Adding a tag a bookmark already has does nothing and doesn't rewrite the file.
- `490f563 bm: add tag command and list --tag` - the two new commands, with CLI tests for success, invalid tag, unknown id, a bad id and a tag added twice.
- `7b3729d docs: tick bookmark tags end-to-end check`

**End-to-end check:** I ran the real CLI against a temp store that started as a pre-tags file:
- `bm tag 2 " Work "` printed `tagged 2 work`.
- `bm list --tag WORK` listed only the tagged bookmarks.
- An unknown id gave `no bookmark 9` (exit 1). An invalid tag gave `invalid tag: to do` (exit 2). A non-numeric id gave `usage: bm tag <id> <tag>` (exit 2).
- The old bookmark gained a `tags` field when the file was next saved.

**Deviation from the plan:** the plan didn't say what `bm list --tag` with no value (or any other extra argument) should do. It now prints `usage: bm list [--tag <tag>]` and exits 2, matching how `add` handles bad input. I added this to the plan's error list.

**How it works:** `run()` in `src/cli.ts` checks the arguments, cleans up the tag with `normalizeTag` (trim, lowercase), and calls `BookmarkStore::tag` or `listByTag`. Those read the file, filter or update, and save. The two error classes are turned into a message and exit code in one place in `run()`, as `AGENTS.md` describes.

Nothing is blocked. I committed with plain `git commit` in the `/commit` skill's format rather than invoking the skill. Nothing has been pushed.