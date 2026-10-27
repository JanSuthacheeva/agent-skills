SHOP-313 is fixed. All 16 tests pass, including a new regression test that failed before the fix.

**Root cause:** `src/store.ts` had a module-level `const noTags: string[] = []`. `fromRecord` used it as the default (`record.tags ?? noTags`) for any bookmark with no `tags` field. That is every bookmark saved before the tagging feature, which matches "since I updated bm". All of those bookmarks therefore shared one array. `tag()` pushes into `bookmark.tags`, so `bm tag 3 recipes` changed the shared array and every untagged bookmark showed the tag. When the file was saved, each of them wrote `recipes` to disk.

**Fix:** I removed `noTags`. `fromRecord` now gives each bookmark its own copy: `tags: [...(record.tags ?? [])]`.

**Test:** I added a test to `test/store.tags.test.ts`. It writes a legacy file with no `tags` fields, tags bookmark 1, and checks that bookmark 2 stays untagged. The existing "load with no tags" test didn't catch this because it creates bookmarks through `add()`, which gives each one its own `[]`.

**Reporter's data:** Their bookmarks file already has the tag saved on all 40 bookmarks. The fix stops new spreading but doesn't undo that. They'll need to remove the wrong tags by hand or edit `.bookmarks.json`. `bm` has no untag command.

I haven't committed anything.