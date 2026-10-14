Bookmark tags are built and working: all five plan tasks are done, 19 tests pass, and the real CLI behaved as planned against a temp store file. The repo has no lint or type-check script, so I ran none. I didn't push anything.

**Commits**
- `bm: normalize tags` was already there from before.
- `bm: store tags on bookmarks`: adds `Bookmark.tags`, new bookmarks start with `[]`, and files written before tags existed load with `[]`.
- `bm: tag bookmarks and filter by tag in the store`: adds `BookmarkNotFoundError`, `BookmarkStore.tag` and `BookmarkStore.listByTag`.
- `bm: add tag command and list --tag`: adds `bm tag <id> <tag>` and `bm list --tag <tag>`.
- `docs: tick bookmark tags e2e check`.

**Deviations from the plan**
- `run` now wraps a new internal `dispatch` function in a try/catch. That one place turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1.
- `bm list --tag` with no tag prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover this case.
- Tagging an already-present tag is a no-op, as the plan assumed.

**End-to-end check**
- `add`, `tag 1 " Work "` (prints `tagged 1 work`) and `list --tag work` (shows only bookmark 1) all worked.
- Unknown id gave `no bookmark 9` with exit 1.
- Invalid tag gave `invalid tag: to do` with exit 2.
- Non-numeric id gave the usage message with exit 2.
- The store file holds `tags: ["work"]` on the tagged bookmark and `tags: []` on the other.

**How it works**
- `main` calls `run`, which calls `dispatch`.
- `dispatch` runs `normalizeTag`, then `BookmarkStore.tag` or `BookmarkStore.listByTag`, and prints.
- The store loads the JSON file, fills in `tags: []` where it's missing, and saves.

Nothing is blocked or left open.