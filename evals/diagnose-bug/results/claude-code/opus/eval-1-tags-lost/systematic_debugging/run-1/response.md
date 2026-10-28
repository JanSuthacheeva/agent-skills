I fixed SHOP-311. `list --tag` was working correctly. The real bug was that adding a bookmark deleted every existing tag from the bookmarks file.

**Root cause:** `toRecord` in `src/store.ts:27`, which turns a bookmark into what gets written to the file, left out `tags`. So every `save()` wrote the file without them, and `add` calls `save()`. `tag()` only kept its tags because it put `tags` back in by hand when writing. I reproduced it with the CLI: after `add`, the `tags` field was gone from the JSON on disk.

The existing tests didn't catch this because they always tag after the last `add`.

**Fix:**
- `toRecord` now includes `tags`.
- `tag()` now just calls `this.save(all)` instead of patching tags in itself.
- I added a regression test in `test/store.tags.test.ts` ("adding a bookmark keeps existing tags"): it tags a bookmark, adds another, then checks the tag is still there. It failed before the fix.

All 16 tests pass, and the reporter's steps (add, tag, add, `list --tag work`) now show the tagged bookmark.

**Can't be recovered:** tags already deleted by an `add` are gone from users' files. The reporter will need to tag those bookmarks again. It's worth saying that when you close the ticket.

I haven't committed the changes or updated the ClickUp ticket.