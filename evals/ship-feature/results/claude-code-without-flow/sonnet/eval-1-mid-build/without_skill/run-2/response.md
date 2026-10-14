The bookmark tags feature is built, and all five plan tasks are ticked. The full suite passes (19 tests). I also ran the real `npm run bm` commands against a temp store file. I didn't push or open a merge request. The repo has no lint or type-check script, so I ran neither.

**Tasks and commits**
- Task 1, `normalizeTag` and `InvalidTagError`: `bfaa882` (already done when I started).
- Task 2, `tags` on `Bookmark` and old files loading as `tags: []`: `a6e3d72`.
- Task 3, `BookmarkNotFoundError`, `tag` and `listByTag`: `362efb8`.
- Task 4, `bm tag` and `bm list --tag`: `a99b367`.
- Task 5, the end-to-end check: `16c3695` (ticks the plan).

**Deviation from the plan**
- I added `usage: bm list [--tag <tag>]` with exit 2 for a malformed `list`, such as `list --tag` with no value or an unknown flag. The plan didn't cover that case, and without it `list --tag` would have silently listed everything. I added the line to the plan's error list. It is a new user-visible message, so say so if you want it removed.

**End-to-end result**
- `tag 2 Runtime` printed `tagged 2 runtime`, and tagging again did nothing.
- `list --tag runtime` listed only the tagged bookmarks, and `list --tag nope` printed nothing.
- Errors were `invalid tag: to-do!` (exit 2), `no bookmark 9` (exit 1) and the usage lines (exit 2).
- The store file holds `tags` on each bookmark.

**How it works**
- `main` calls `run`, which now wraps a private `dispatch` function in a try/catch.
- The catch turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1.
- `tag` and `list --tag` call `normalizeTag` first, then `BookmarkStore.tag` or `listByTag`.
- `tag` adds the tag only if it's missing and saves.
- `load()` reads any bookmark without a `tags` field as `tags: []`.

Nothing is blocked or left open.