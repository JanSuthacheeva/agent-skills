I fixed SHOP-311. The ticket blames `list --tag`, but that part works. The real problem is that adding a bookmark deleted every existing tag from the file.

**Cause:** `toRecord` in `src/store.ts:27` converts a bookmark to what's saved on disk, and it didn't include `tags`. Every save goes through it, so `bm add` rewrote the file without any tags. `tag()` didn't have the problem because it added the tags back in by hand before writing. That's why tagging seemed to work and the tags only vanished on the next `add`. I reproduced this with the CLI: right after `bm tag 1 work` the file had `"tags": ["work"]`, and after the next `bm add` it was gone.

**Fix:**
- `toRecord` now saves `tags`.
- `tag()` now uses the normal `save()`, since the hand-written workaround isn't needed anymore.

**Test:** I added "adding a bookmark keeps existing tags" to `test/store.tags.test.ts`: tag a bookmark, add another, then list by tag. It failed before the fix and passes now. All 16 tests pass, and the reproduction from the ticket now lists the tagged bookmark.

**For the reporter:** tags erased before this fix are gone from their bookmarks file and can't be recovered, so they'll need to tag those bookmarks again.

I haven't committed anything or updated the ClickUp ticket.