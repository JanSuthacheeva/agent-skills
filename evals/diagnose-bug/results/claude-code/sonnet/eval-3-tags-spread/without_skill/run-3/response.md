SHOP-313 is fixed: tagging one bookmark no longer tags the others. All 16 tests pass.

**Cause:** `fromRecord` in `src/store.ts` gave every bookmark saved before tags existed (no `tags` field) the same module-level `noTags` array. `store.tag(3, 'recipes')` pushed onto that shared array, so every untagged legacy bookmark got the tag. The CLI wasn't ignoring the id, as the reporter guessed.

**Fix:** `fromRecord` now creates a fresh `[]` for each bookmark, and I removed the `noTags` constant.

**Test:** I added a regression test in `test/store.tags.test.ts`. It loads a legacy file with no `tags` fields, tags bookmark 3, and checks that only bookmark 3 has the tag. I didn't run it against the old code to confirm it fails there.

Bookmarks the reporter already tagged were saved to disk with the tag on all of them. They'll need to remove those tags by hand, because `bm` has no untag command.