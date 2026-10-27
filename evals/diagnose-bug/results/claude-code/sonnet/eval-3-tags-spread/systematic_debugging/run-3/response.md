SHOP-313 is fixed: `bm tag 3 recipes` now tags only bookmark 3. The full suite passes (16 tests), including a new regression test.

**Root cause:** in `src/store.ts`, `fromRecord` gave every bookmark saved before tagging existed (no `tags` field in the file) the same module-level `noTags` array. `tag()` pushes onto that array, so the tag landed on every untagged bookmark at once. The tag command did use the id correctly. This is why only people with older bookmark files, like the reporter, saw it. Bookmarks added after the tagging feature always got their own array.

**Reproduction:** I made a two-bookmark file with no `tags` fields, ran `tag 1 recipes`, and `list --tag recipes` returned both bookmarks.

**Fix:** `record.tags ?? []` now creates a fresh array per bookmark, and I removed `noTags`.

**Test:** I added `tagging a bookmark from a file without tags does not tag the others` to `test/store.tags.test.ts`. It failed before the fix and passes now.

**Existing data:** anyone already hit by this has the wrong tags saved in their file. Those need removing by hand. I didn't touch any bookmarks files.

I haven't committed anything.