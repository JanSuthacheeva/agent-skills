I fixed SHOP-311. Tags were being lost when a new bookmark was added, and `bm list --tag` was never the problem. All 16 tests pass, including a new regression test.

**Cause:** `toRecord` in `src/store.ts` left `tags` out of the saved record. `add()` loads all bookmarks and calls `save()`, so every existing bookmark was rewritten without its tags. Only `tag()` wrote tags, because it built its own records.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now calls `this.save(all)` instead of building its own records.
- The new test in `test/store.tags.test.ts` tags a bookmark, adds another, and checks the tag is still there.

Bookmarks that already lost their tags can't be recovered. They need to be re-tagged.

I haven't committed anything or updated the ClickUp ticket.