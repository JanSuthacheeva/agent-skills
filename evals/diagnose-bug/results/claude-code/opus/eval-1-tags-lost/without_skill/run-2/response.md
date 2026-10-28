SHOP-311 is fixed. `list --tag` was never broken: running `bm add` was deleting every tag in the bookmarks file.

**Cause:** in `src/store.ts`, `toRecord` turns a bookmark into what gets written to the file, and it left out `tags`. `add` saves through it, so any `bm add` rewrote the file without tags. `bm tag` only seemed to work because it bypassed this and added the tags back by hand before writing. I reproduced it with the CLI: tag bookmark 1 as `work`, add bookmark 2, and the file no longer has any tags.

**Fix** (`src/store.ts`):
- `toRecord` now includes `tags`.
- `tag()` now saves through the normal `save()` path instead of its workaround.

**Test:** I added "adding a bookmark keeps existing tags" to `test/store.tags.test.ts`. It fails without the fix and passes with it. All 16 tests pass.

The fix doesn't bring back tags that have already been lost. The reporter will need to re-tag the bookmarks they tagged before their last `bm add`. Nothing is committed yet.