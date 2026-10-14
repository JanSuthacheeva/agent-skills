Bookmark tags are built, and all five tasks in the plan are checked off. `npm test` passes with 18 tests, and I ran the real CLI against a temp store file.

**What now works**
- **Storage:** bookmarks carry a `tags` array. Store files written before this change load with `tags: []`, so no migration is needed.
- **Store:** `BookmarkStore` has `tag(id, tag)` and `listByTag(tag)`, plus `BookmarkNotFoundError`. Tagging twice with the same tag does nothing.
- **CLI:**
  - `bm tag <id> <tag>` prints `tagged <id> <tag>`.
  - `bm list --tag <tag>` lists only the matching bookmarks.
  - Both accept input like `" Work "` and store it as `work`.
- **Errors:** an invalid tag prints `invalid tag: <raw>` and exits 2. An unknown id prints `no bookmark <id>` and exits 1. A non-numeric id prints the usage line and exits 2.

**Beyond the plan**
- `run` is now a thin wrapper that maps the two error classes to messages and exit codes.
- `bm list --tag` with no tag prints `usage: bm list [--tag <tag>]` and exits 2.

The work is in four commits on `feature/bookmark-tags`, plus a docs commit that ticks the plan. Nothing is pushed and no merge request is open.