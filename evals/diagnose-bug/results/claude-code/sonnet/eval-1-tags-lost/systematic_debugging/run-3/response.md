SHOP-311 is fixed. `bm list --tag work` was never broken. Adding a bookmark was erasing the tags on every existing bookmark.

**Root cause:** `toRecord` in `src/store.ts` left `tags` out of the record it serialises. `add()` rewrites the whole file through `save()`, which uses `toRecord`, so each `bm add` dropped all existing tags from the file. `tag()` was unaffected because it added `tags` back by hand when writing. That is why the tags survived until the next `add`.

**Reproduction:** I added a bookmark, tagged it `work`, then added another. The file showed `tags` after the `tag` step and no `tags` after the second `add`.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now calls `save(all)` instead of its own special-case write.
- I added a regression test, `adding a bookmark keeps the tags of existing ones`, in `test/store.tags.test.ts`. It failed before the fix. All 16 tests pass now.

Bookmarks whose tags were already lost can't be recovered from the file. Users will need to re-tag them. I haven't committed anything.