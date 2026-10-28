I fixed SHOP-311. The ticket blames `list --tag`, but that command works: the tags were actually being deleted from the bookmarks file whenever a new bookmark was added.

**Cause:** in `src/store.ts`, the function that converts a bookmark into what gets written to disk (`toRecord`) left out `tags`. `add()` saves the whole list through that function, so every add rewrote the file without anyone's tags. `tag()` only worked because it put the tags back in by hand before writing. I reproduced it: tag bookmark 1 as `work`, add bookmark 2, and the file no longer contains any tags, so `list --tag work` prints nothing.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now saves through the normal `save()` path, so the workaround is gone.
- I added a regression test in `test/store.tags.test.ts`: tag a bookmark, add another, check that the tag is still there.

All 16 tests pass, and the reproduction steps now print bookmark 1 from `list --tag work`.

The fix can't recover tags that were already lost. Anyone who added a bookmark after tagging will need to tag those bookmarks again, so it's worth saying that in the reply on the ticket. Nothing is committed yet.