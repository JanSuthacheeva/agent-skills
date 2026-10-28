SHOP-311 is fixed, and all 16 tests pass, including the new regression test. `list --tag` itself was fine. The bug was in how the store saved bookmarks.

**Cause:** `toRecord` in `src/store.ts` didn't write `tags`. `add()` saves through it, so adding a bookmark wiped the tags on every existing one. `tag()` was the only path that kept tags, because it wrote them back by hand.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now calls `this.save(all)` instead of its own special-case write.
- I added the test `adding a bookmark keeps existing tags` in `test/store.tags.test.ts`.

Bookmarks whose tags were already wiped by an earlier `add` can't be recovered by this change. Those tags need to be re-applied.