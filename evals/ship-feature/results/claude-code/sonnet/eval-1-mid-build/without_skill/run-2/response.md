The bookmark tags feature is built and all five plan tasks are ticked. All 17 tests pass and the working tree is clean. The repo has no lint or type-check script, so I didn't run either. I haven't pushed anything.

**Commits**
- `6234ef4` adds the `tags` field to bookmarks. Files written before tags existed load as `tags: []`.
- `5ffa512` adds `BookmarkNotFoundError`, `BookmarkStore.tag` and `BookmarkStore.listByTag`.
- `42d29b0` adds `bm tag <id> <tag>` and `bm list --tag <tag>`.
- A final docs commit ticks the end-to-end task.

**End-to-end check** against a temp `BM_FILE`:
- `tag 2 Work` printed `tagged 2 work`, and tagging `work` again was a no-op.
- `list --tag work` printed only bookmark 2.
- `tag 9 x` printed `no bookmark 9` (exit 1).
- `tag 1 "to do"` printed `invalid tag: to do` (exit 2).
- `tag x y` printed the usage line (exit 2).
- The store file keeps its JSON-array format, with `tags` on each bookmark.

**Deviations from the plan**
- I added a usage error, `usage: bm list [--tag <tag>]` with exit 2, for `list --tag` with no value. The plan didn't cover that case.
- `run` now wraps a private `dispatch` function in one `try/catch`. That `try/catch` maps `InvalidTagError` to exit 2 and `BookmarkNotFoundError` to exit 1.

**How it works:** `main` calls `run`, which calls `dispatch`. For `tag`, it calls `store.tag(id, tag)`, which normalizes the tag with `normalizeTag`, loads the bookmarks, adds the tag if it's missing, and saves. For `list --tag`, `store.listByTag(tag)` normalizes the tag and filters the loaded bookmarks.

Nothing is blocked or left open.