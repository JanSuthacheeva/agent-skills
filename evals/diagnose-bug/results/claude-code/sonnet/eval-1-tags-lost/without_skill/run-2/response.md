SHOP-311 is fixed: tags no longer disappear when you add a bookmark. `bm list --tag` was never broken. All 16 tests pass.

**Cause:** `toRecord` in `src/store.ts` left `tags` out of the saved record. `add` loads every bookmark and writes them all back through `save`, so each add wiped all tags from the file. Only `tag()` wrote tags, because it built its own records.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now calls `this.save(all)` instead of building its own records.
- I added a regression test in `test/store.tags.test.ts`: tag a bookmark, add another, and the tag is still listed. I didn't run it against the old code to confirm it fails there.

Tags already lost from an existing bookmarks file can't be recovered. They'll need to be re-added.

I haven't committed anything.