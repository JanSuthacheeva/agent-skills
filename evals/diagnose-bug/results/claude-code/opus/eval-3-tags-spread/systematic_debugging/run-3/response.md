I fixed SHOP-313. The tag command does use the id; the bug was in how the store loads older bookmarks.

**Cause:** In `src/store.ts`, `fromRecord` gave every bookmark whose record has no `tags` field the same module-level `noTags` array. Bookmarks saved before the tagging update (commit `a1f18b2`) don't have that field. So `bm tag 3 recipes` pushed `recipes` into the one array all those bookmarks pointed to, and the save then wrote the tag onto every one of them. Bookmarks created after the update each get their own array, which is why the existing tests passed and why it only shows up "since I updated".

**How I confirmed it:** I made a bookmarks file in the old format with no `tags` fields and ran `bm tag 3 recipes`. Then `bm list --tag recipes` listed every bookmark. Newly added bookmarks tagged correctly.

**Fix:**
- `tags: record.tags ?? []` now gives each loaded bookmark its own array, and I removed the shared `noTags` constant.
- I added a test in `test/store.tags.test.ts` that writes a file in the old format, tags one bookmark, and checks that only that one comes back. It failed before the fix and passes now. All 16 tests pass, and the CLI reproduction now lists only bookmark 3.
- The existing test "bookmarks saved before tags load with no tags" doesn't test what its name says: it creates the bookmark with `add`, so the record already has `tags: []` and the old format never gets loaded. My new test is the one that exercises that path.

**Still to handle:** The fix stops new spreading but doesn't repair files that are already affected. The reporter's file has `recipes` saved on all 40 bookmarks, and there's no untag command, so they'll need to edit the file by hand or we'd need a cleanup step. I haven't committed anything or updated the ticket.