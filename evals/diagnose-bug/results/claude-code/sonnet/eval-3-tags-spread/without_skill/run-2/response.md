SHOP-313 is fixed: tagging one bookmark no longer tags the others, and `npm test` passes (16 tests).

**Cause:** In `src/store.ts`, `fromRecord` gave every bookmark without a `tags` field the same module-level `noTags` array. Bookmarks saved before tags existed have no `tags` field, so they all shared one array. `bm tag 3 recipes` pushed onto that shared array, and every other old bookmark picked up the tag. Because the file is rewritten on save, the tag was then stored on all of them.

**Fix:** `fromRecord` now builds a fresh array for each bookmark with `tags: [...(record.tags ?? [])]`, and I removed `noTags`.

**Test:** I added a regression test in `test/store.tags.test.ts`. It writes two old-format bookmarks, tags one, and checks the other has no tags. The existing "load with no tags" test never covered this because it used a bookmark created by the current code, which already has a `tags` array.

**Existing data:** Files already damaged, like the reporter's 40 bookmarks, still have the tag saved on every bookmark. The reporter will need to clear it by hand. I didn't add a cleanup command.