Bookmark tags is finished: `bm tag <id> <tag>` and `bm list --tag <tag>` work. All 16 tests pass, and I tested it by running the real CLI against a temporary store file. The project has no lint or type-check scripts, so neither was run.

**Commits (picking up after "normalize tags"):**
- `18bccfa` bm: store tags on bookmarks
- `7cfa368` bm: tag bookmarks and list them by tag
- `70a5568` bm: add tag command and list --tag
- `4be652c` docs: check bookmark tags end to end (ticks the last task in the plan)

**What the CLI check showed:**
- **Tag spelling:** ` Runtime `, `Runtime` and `RUNTIME` all become `runtime`.
- **Repeats:** tagging a bookmark again with a tag it already has does nothing.
- **Filtering:** `list --tag` prints only the tagged bookmarks, in the same format as `list`.
- **Errors:**
  - an unknown id prints `no bookmark 9` and exits 1
  - a non-numeric id prints the usage line and exits 2
  - `to do` prints `invalid tag: to do` and exits 2
- **Old files:** a store file written before tags existed loads fine, and the next write adds the `tags` field. No migration is needed.

**Changes from the plan (both small; the plan is updated to match):**
- **Error handling in one place:** in `src/cli.ts`, the command handling moved into a private `dispatch()`. `run()` now turns `InvalidTagError` and `BookmarkNotFoundError` into the messages and exit codes in one spot.
- **Missing arguments:** the plan didn't cover these. `bm tag <id>` with no tag prints `usage: bm tag <id> <tag>`. `bm list --tag` with no tag, or with another option, prints `usage: bm list [--tag <tag>]`. Both exit 2, like `add` does. These messages are visible to users, so say if you want them different.

Nothing is blocked or left open.

**How it works:** `main.ts` calls `run()` with a store for the file in `BM_FILE` (or `~/.bookmarks.json` if unset). For `tag` and `list --tag`, `run()` cleans up the tag with `normalizeTag()` in `src/tags.ts`, which rejects anything empty or outside `a-z0-9-`. It then calls `BookmarkStore.tag()` or `listByTag()` in `src/store.ts`. The store loads the file, treating a missing `tags` field as empty. `tag()` adds the tag if it isn't there yet and saves; `listByTag()` returns only the bookmarks with that tag.

Nothing has been pushed and no merge request is open.