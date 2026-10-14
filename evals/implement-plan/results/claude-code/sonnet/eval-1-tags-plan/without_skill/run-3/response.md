Bookmark tags are implemented as planned. All 18 tests pass, and I ran `add`, `tag` and `list --tag` against a temp store file. The tagged bookmark showed up under `list --tag`. Tagging it twice didn't add a duplicate, and tagging an unknown id printed `no bookmark 5` and exited 1.

- **`src/tags.ts`:** `normalizeTag` trims, lowercases and rejects anything outside `a-z`, `0-9` and `-`.
- **`Bookmark`:** it now has `tags`. New bookmarks start with `tags: []`, and `load()` reads files written before tags existed as `[]`.
- **`src/store.ts`:** `BookmarkStore` has `tag(id, tag)` and `listByTag(tag)`.
- **`bm tag <id> <tag>`:** exits 2 for a non-numeric id or an invalid tag, and 1 for an unknown id.
- **`bm list --tag <tag>`:** exits 2 for an invalid tag.
- **Plan file:** I ticked the task boxes in `docs/plans/2026-10-14-bookmark-tags.md`.

The `/commit` skill wasn't available in this session, so I committed with plain git as `08528c8`. It's a single commit for the whole feature, not one per task.