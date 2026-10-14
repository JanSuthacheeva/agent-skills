I've implemented the bookmark tags plan in four commits, one per task, and ticked off the tasks in the plan in a fifth commit. All 21 tests pass.

- **`src/tags.ts`:** `normalizeTag` trims and lowercases the input. It throws `InvalidTagError` if the result is empty or has characters other than `a-z`, `0-9` and `-`.
- **`src/bookmark.ts`, `src/store.ts`:**
  - Bookmarks now have a `tags` field, and new ones start with no tags.
  - Files written before this change load with empty tags, so no migration is needed.
  - `tag(id, tag)` adds a tag. Adding one the bookmark already has does nothing, and an unknown id throws `BookmarkNotFoundError`.
  - `listByTag(tag)` returns only the bookmarks with that tag.
- **`src/cli.ts`:** adds `bm tag <id> <tag>` and `bm list --tag <tag>`. A bad tag prints `invalid tag: <raw>` (exit 2), an unknown id prints `no bookmark <id>` (exit 1), and a non-numeric id prints the usage line (exit 2).

I also ran the real CLI against a temp store file: `add`, `tag` (including re-tagging, an unknown id, an invalid tag and a non-numeric id), `list` and `list --tag` all gave the expected output and exit codes. The saved file had the `tags` field in the right shape.

Three things the plan didn't specify:
- `bm list` with any other arguments, such as `--tag` with no value, now prints `usage: bm list [--tag <tag>]` and exits 2. Before, it ignored extra arguments.
- `bm tag` with too few or too many arguments prints its usage line and exits 2.
- The store's `tag` and `listByTag` don't normalize tags themselves; they expect the CLI to have done it, as in the plan's call chains. Anything else that calls the store would have to normalize first.

There's no TypeScript type checker set up in this repo (Node just strips the types when it runs), so the types weren't checked beyond Node running the code.