Bookmark tags are built: `bm tag <id> <tag>` and `bm list --tag <tag>` both work. All 5 plan tasks are done and ticked, all 23 tests pass, and I ran the real CLI against a temporary store file to check it end to end. The project has no lint or type-check setup, so neither was run.

**Commits**
- `2224c11` adds `normalizeTag` and `InvalidTagError` (`src/tags.ts`).
- `c95c8f0` adds `Bookmark.tags`. New bookmarks start with no tags, and files saved before this change load with no tags.
- `2940474` adds `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`.
- `94ee7c4` adds the `tag` command and the `list --tag` option to the CLI.
- `ce34708` ticks the end-to-end check in the plan.

**End-to-end check:** I started from a store file in the old format (no `tags` field) and used `npm run bm` to add, tag and filter bookmarks:
- `tag 2 " Work "` printed `tagged 2 work`, and repeating it was a no-op.
- `list --tag WORK` printed only the bookmark tagged `work`, in the same format as `list`.
- The old bookmark could be tagged too.
- The error cases printed the planned messages and exit codes: `no bookmark 9` (1), `usage: bm tag <id> <tag>` (2), `invalid tag: c++` (2).
- The file stayed a JSON array, now with a `tags` field.

**Changes from the plan (both written back into it):**
- **New usage error:** `bm list` with anything other than `--tag <tag>` (for example `--tag` with no value) prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover this case; I followed the existing `add` usage error.
- **Internal split:** `run` now wraps a private `dispatch` function, so turning errors into messages and exit codes happens in one place. The error message itself is the CLI text (`invalid tag: <raw>`, `no bookmark <id>`), so the CLI prints it as is.

**Other notes:**
- The `/commit` skill isn't available in this environment, so I committed with plain git in the repo's `bm: ...` message style.
- Nothing is blocked or left open, and nothing was pushed.

**How it works:**
1. `src/main.ts` calls `run(argv, store, out)`.
2. `dispatch` parses the command. For `tag`, it checks the id is a number, then `normalizeTag` trims and lowercases the tag, and rejects it if anything outside `a-z0-9-` remains.
3. `BookmarkStore::tag` loads the file, adds the tag if it isn't there yet, and saves. An unknown id raises `BookmarkNotFoundError`.
4. `list --tag` normalizes the tag the same way and prints `listByTag`'s results with the existing `format`.
5. `load()` fills in `tags: []` for old records, so old files work without a migration.