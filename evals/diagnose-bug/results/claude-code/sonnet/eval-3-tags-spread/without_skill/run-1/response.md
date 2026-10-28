SHOP-313 is fixed in `src/store.ts`, and the existing 15 tests pass. I didn't add a regression test.

**Cause:** `fromRecord` gave every bookmark with no `tags` field the same shared array, `noTags`. Bookmarks saved before tags existed have no `tags` field. `bm tag 3 recipes` pushed onto that shared array, so every such bookmark got `recipes` on the next save. That matches the reporter's "since I updated" and their 40 results.

**Fix:** I removed the `noTags` constant and made `fromRecord` use `record.tags ?? []`, so each bookmark gets its own array.

**Existing data:** files already affected will have the tag written on every bookmark. Those bookmarks need the extra tags removed by hand, because the code can't tell which tag was meant for which bookmark. `bm` has no untag command.

I can add a regression test (load a file with tagless records, tag one, check the others) if you want.