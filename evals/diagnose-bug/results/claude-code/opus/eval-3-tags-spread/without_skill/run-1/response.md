I fixed SHOP-313. The ticket guessed that the tag command ignores the id, but it doesn't. The id is used correctly; the bug is in how bookmarks are loaded.

**Cause:** In `src/store.ts`, `fromRecord` filled in missing tags with one shared module-level array (`noTags`). Bookmarks saved by the old version have no `tags` field, so after loading, all of them pointed at that same array. When `tag()` pushed `recipes` onto bookmark 3's tags, it was pushing onto the array every old bookmark shared, and `save()` then wrote `recipes` to all of them. That's why it only started after the update, and why the reporter saw all 40 bookmarks tagged.

The existing tests missed it because every test bookmark is created by `add()`, which gives each one its own `tags: []`.

**Fix:**
- **`src/store.ts`:** I removed `noTags`, so `fromRecord` now uses `record.tags ?? []` and each bookmark gets its own array.
- **`test/store.tags.test.ts`:** I added a regression test that writes a bookmarks file in the old format (no `tags` key), tags one bookmark, and checks that only that one comes back from `listTagged`. It failed before the fix and passes now; all 16 tests pass.
- **CLI check:** I ran `bm tag 3 recipes` against an old-format file, and `bm list --tag recipes` now shows only bookmark 3.

**The fix won't repair existing files.** Anyone who already tagged a bookmark with the buggy version has the wrong tags saved on all their old bookmarks. For the reporter, that's `recipes` on all 40. Those tags need removing by hand, or with a small cleanup script, since there's no untag command yet. I can write a script if that's useful.

I haven't committed anything.