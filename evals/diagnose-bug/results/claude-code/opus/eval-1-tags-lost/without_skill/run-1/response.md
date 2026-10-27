I fixed SHOP-311. The ticket blames `list --tag`, but that command works fine. The real problem was that adding a bookmark erased every tag from the bookmarks file, so `list --tag work` had nothing to find.

**Cause:** `toRecord` in `src/store.ts` turns a bookmark into what gets written to the file, and it left out `tags`. `tag()` didn't notice because it added the tags back in by hand before writing. `add()` went through the normal save, so every add rewrote the file without any tags. I reproduced this with the CLI: tag bookmark 1, add bookmark 2, and the file no longer has any tags.

**Fix** (`src/store.ts`):
- `toRecord` now includes `tags`.
- `tag()` now uses the normal `save()` instead of its own workaround, so tags are written the same way everywhere.

**Test:** I added a regression test in `test/store.tags.test.ts` ("adding a bookmark keeps existing tags"). All 16 tests pass, and the CLI repro now lists the tagged bookmark after another one is added. I didn't check that the new test fails on the old code.

The fix can't bring back tags that were already erased, so the reporter will need to re-tag those bookmarks. You may want to say that when you reply on the ticket. I haven't committed anything or updated ClickUp.