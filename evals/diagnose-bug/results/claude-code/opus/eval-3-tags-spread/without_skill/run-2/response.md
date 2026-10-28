I've fixed SHOP-313 in `src/store.ts` and added a regression test. The new test failed before the fix and all 16 tests pass now. Nothing is committed yet.

**Cause:** The tag command does use the id. The problem was in how bookmarks are loaded. Bookmarks saved before the tagging update (`4706200`) have no `tags` field in the file, and the code gave all of them the same shared empty list (`noTags`). Adding a tag to one of those bookmarks added it to that shared list, so every pre-update bookmark got the tag and it was saved that way. That's why the reporter saw all 40 bookmarks. Bookmarks added after the update weren't affected, which is why the existing tests didn't catch it: they only create bookmarks through `add()`.

**Fix:**
- Each bookmark loaded without tags now gets its own empty list, and the shared `noTags` list is gone.
- `tag()` now builds a new list instead of changing the existing one, so a shared list can't cause this again.
- New test in `test/store.tags.test.ts`: it writes a bookmarks file in the pre-update format, tags one bookmark and checks that only that bookmark has the tag.

**Decision for you:** the fix doesn't repair files that are already wrong. The reporter's file now has `recipes` saved on all 40 bookmarks, and there's no way to tell from the file which one they actually tagged. They'll need to fix it by hand: remove the tag from the wrong bookmarks, or delete the tags from the pre-update bookmarks and tag the right one again. There's no `untag` command yet, so it may be worth adding one. Should I add it or reply on the ticket?